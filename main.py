from nicegui import ui
import base64
import httpx
import zlib
import string

from multiprocessing import freeze_support

freeze_support()

# https://plantuml.com/text-encoding
# https://github.com/dougn/python-plantuml/blob/master/plantuml.py#L64

# PLANTUML_SERVER = "http://www.plantuml.com/plantuml/"
PLANTUML_SERVER = "http://127.0.0.1:8000/plantuml/"

maketrans = bytes.maketrans

plantuml_alphabet = (
    string.digits + string.ascii_uppercase + string.ascii_lowercase + "-_"
)
base64_alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"
b64_to_plantuml = maketrans(
    base64_alphabet.encode("utf-8"), plantuml_alphabet.encode("utf-8")
)
plantuml_to_b64 = maketrans(
    plantuml_alphabet.encode("utf-8"), base64_alphabet.encode("utf-8")
)


def plantuml_encode(plantuml_text):
    """zlib compress the plantuml text and encode it for the plantuml server"""
    zlibbed_str = zlib.compress(plantuml_text.encode("utf-8"))
    compressed_string = zlibbed_str[2:-4]
    return (
        base64.b64encode(compressed_string).translate(b64_to_plantuml).decode("utf-8")
    )


def plantuml_decode(plantuml_url):
    """decode plantuml encoded url back to plantuml text"""
    data = base64.b64decode(plantuml_url.translate(plantuml_to_b64).encode("utf-8"))
    dec = zlib.decompressobj()  # without check the crc.
    header = b"x\x9c"
    return dec.decompress(header + data).decode("utf-8")


@ui.page("/")
async def index():
    def get_url() -> tuple[str, str]:
        uml_str = uml_code.value

        # Apply high-quality settings for PNG format
        if toggle1.value == "PNG":
            # Add @startuml and @enduml if not present
            if "@startuml" not in uml_str:
                uml_str = "@startuml\n" + uml_str
            if "@enduml" not in uml_str:
                uml_str = uml_str + "\n@enduml"

            # Insert high-quality directives after @startuml
            lines = uml_str.split("\n")
            start_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("@startuml"):
                    start_idx = i + 1
                    break

            # Insert quality improvement directives
            quality_directives = ["skinparam dpi 400", "scale 2"]

            for directive in quality_directives:
                lines.insert(start_idx, directive)
                start_idx += 1

            uml_str = "\n".join(lines)

        img_src = PLANTUML_SERVER
        img_src += "svg/" if toggle1.value == "SVG" else "png/"
        base64_prefix = (
            "data:image/svg+xml;base64,"
            if toggle1.value == "SVG"
            else "data:image/png;base64,"
        )

        uml_encoded = plantuml_encode(uml_str)
        return img_src + uml_encoded, base64_prefix

    async def fetch_image(*args):
        try:
            # Save current code to local storage using JavaScript
            ui.run_javascript(
                f"localStorage.setItem('plantuml_code', {repr(uml_code.value)})"
            )

            url, base64_prefix = get_url()
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    print("Request successful!")
                    image_base64 = base64.b64encode(response.content).decode("utf-8")
                    image_base64 = base64_prefix + image_base64
                    uml_img.set_source(image_base64)
                    return image_base64
                else:
                    print(f"Request failed, status code: {response.status_code}")
        except httpx.RequestError as e:
            print(f"Request error: {e}")
        except httpx.HTTPError as e:
            print(f"HTTP ERROR: {e}")
        except Exception as e:
            print(e)
        return None

    toggle1 = ui.toggle(["SVG", "PNG"], value="SVG", on_change=fetch_image)
    # Add CSS for the resizable layout
    ui.add_head_html("""
    <style>
        .resizable-container {
            display: flex;
            width: 100%;
            height: 90vh; /* 90% of viewport height */
            overflow: hidden;
        }
        .resizable-panel {
            overflow: auto;
            min-width: 10%;
            box-sizing: border-box;
        }
        .left-panel {
            width: 40%;
        }
        .right-panel {
            width: 60%;
        }
        .resizable-handle {
            width: 8px;
            background-color: #ddd;
            cursor: col-resize;
            transition: background-color 0.2s;
        }
        .resizable-handle:hover {
            background-color: #aaa;
        }
        .full-height-textarea .q-field__control {
            height: 100% !important;
        }
        .full-height-textarea .q-field__native {
            height: 100% !important;
            min-height: 100% !important;
        }
    </style>
    """)

    # Create a container with custom classes for resizable layout
    image_container = ui.element("div").classes("resizable-container")

    with image_container:
        # Left panel with textarea
        left_panel = ui.element("div").classes("resizable-panel left-panel")
        with left_panel:
            # Default code to use if no saved code is found
            default_code = "Alice -> Bob: hello"

            # Create the textarea with default code initially
            uml_code = (
                ui.textarea(
                    label="PlantUML Code",
                    placeholder="Edit plantuml here",
                    value=default_code,
                    on_change=fetch_image,
                )
                .classes("full-height-textarea")
                .style("width: 100%; height: 100%")
            )

            # Try to load saved code from localStorage using JavaScript
            ui.run_javascript("""
            try {
                const savedCode = localStorage.getItem('plantuml_code');
                if (savedCode) {
                    // Update the textarea with the saved code
                    const textareaElement = document.querySelector('.full-height-textarea textarea');
                    if (textareaElement) {
                        textareaElement.value = savedCode;
                        // Trigger change event to update the diagram
                        const event = new Event('input', { bubbles: true });
                        textareaElement.dispatchEvent(event);
                    }
                }
            } catch (e) {
                console.error('Error loading saved code:', e);
            }
            """)

        # Resizable handle
        ui.element("div").classes("resizable-handle")

        # Right panel with image
        right_panel = ui.element("div").classes("resizable-panel right-panel")
        with right_panel:
            uml_img = ui.image("./hello.svg").style("width: 100%; height: auto;")

        # Add JavaScript for resizable functionality
        ui.add_body_html("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.querySelector('.resizable-container');
            const leftPanel = container.querySelector('.left-panel');
            const rightPanel = container.querySelector('.right-panel');
            const handle = container.querySelector('.resizable-handle');
            let isResizing = false;
            let lastX;
            
            handle.addEventListener('mousedown', function(e) {
                isResizing = true;
                lastX = e.clientX;
                document.addEventListener('mousemove', handleMouseMove);
                document.addEventListener('mouseup', handleMouseUp);
                e.preventDefault();
            });
            
            function handleMouseMove(e) {
                if (!isResizing) return;
                const dx = e.clientX - lastX;
                const leftPanelWidth = leftPanel.getBoundingClientRect().width;
                const containerWidth = container.getBoundingClientRect().width;
                const newLeftWidth = (leftPanelWidth + dx) / containerWidth * 100;
                
                // Limit the minimum and maximum width
                if (newLeftWidth > 10 && newLeftWidth < 90) {
                    leftPanel.style.width = `${newLeftWidth}%`;
                    // Explicitly set the right panel width to fill the remaining space
                    rightPanel.style.width = `${100 - newLeftWidth}%`;
                    lastX = e.clientX;
                }
            }
            
            function handleMouseUp() {
                isResizing = false;
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            }
        });
        </script>
        """)


ui.run(
    storage_secret="private key",
    title="PlantUML",
    favicon="🚀",
    reload=False,
    port=8080,
)
# ui.run(title='PlantUML', favicon='🚀', reload=False, port=native.find_open_port())
