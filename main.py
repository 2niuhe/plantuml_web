from nicegui import ui
import base64
import httpx
import zlib
import string

from multiprocessing import freeze_support
freeze_support()

# https://plantuml.com/text-encoding
# https://github.com/dougn/python-plantuml/blob/master/plantuml.py#L64

maketrans = bytes.maketrans

plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet   = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))
plantuml_to_b64 = maketrans(plantuml_alphabet.encode('utf-8'), base64_alphabet.encode('utf-8'))

def plantuml_encode(plantuml_text):
    """zlib compress the plantuml text and encode it for the plantuml server"""
    zlibbed_str = zlib.compress(plantuml_text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(b64_to_plantuml).decode('utf-8')

def plantuml_decode(plantuml_url):
    """decode plantuml encoded url back to plantuml text"""
    data = base64.b64decode(plantuml_url.translate(plantuml_to_b64).encode("utf-8"))
    dec = zlib.decompressobj() # without check the crc.
    header = b'x\x9c'
    return dec.decompress(header + data).decode("utf-8")

def get_url() -> str:
    uml_str = uml_code.value
    img_src = PLANTUML_SERVER
    img_src += 'svg/' if toggle1.value == 'SVG' else 'png/'
    base64_prefix = 'data:image/svg+xml;base64,' if toggle1.value == 'SVG' else 'data:image/png;base64,'
    
    uml_encoded = plantuml_encode(uml_str)
    return img_src + uml_encoded, base64_prefix

async def fetch_image(*args):
    try:
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

toggle1 = ui.toggle(['SVG', 'PNG'], value='SVG', on_change=fetch_image)
image_container = ui.row().classes("w-full flex")

# PLANTUML_SERVER = "http://www.plantuml.com/plantuml/"
PLANTUML_SERVER = "http://127.0.0.1:8000/plantuml/"

with image_container:
    uml_code = ui.textarea(
        label='PlantUML Code',
        placeholder='Edit plantuml here',
        value='Alice -> Bob: hello',
        on_change=fetch_image).style(
            'flex:1; width: 40%;')

    uml_img = ui.image(
        './hello.svg',
        ).style('min-height: 100%; height: auto; flex: 1;')

ui.run(storage_secret='private key', title='PlantUML', favicon='🤖', reload=False, port=8080)
#ui.run(title='PlantUML', favicon='🤖', reload=False, port=native.find_open_port())
