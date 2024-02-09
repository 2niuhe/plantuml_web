# plantuml_web
Using nicegui as a PlantUML frontend, you can deploy PlantUML on an intranet.

It's a nicegui demo project.

Plantuml jar version: plantuml-1.2024.1.jar

![demo](https://github.com/2niuhe/plantuml_web/blob/main/demo_img/demo.png)
## Usage:

- with docker

```shell
docker build -t nicegui_plantuml .
docker run -d -p 8080:8080 nicegui_plantuml
```

Then you can visit http://127.0.0.1:8080

- without docker

```shell
pip install -r requirements.txt
sh start.sh
```


### ref

[Home · zauberzeug/nicegui Wiki](https://github.com/zauberzeug/nicegui/wiki)

[How to use nicegui for beginners？ · zauberzeug/nicegui · Discussion #1486](https://github.com/zauberzeug/nicegui/discussions/1486)

[Nicegui example and suggestions · zauberzeug/nicegui · Discussion #1778](https://github.com/zauberzeug/nicegui/discussions/1778)

[NiceGUI](https://nicegui.io/documentation)

[syejing/nicegui-reference-cn: NiceGUI 中文版本文档](https://github.com/syejing/nicegui-reference-cn?tab=readme-ov-file)

[(1) Use NiceGUI to watch images and do it from the COMMAND LINE! - YouTube](https://www.youtube.com/watch?v=eq0k642zQQ8)
