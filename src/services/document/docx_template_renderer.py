from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


class DocxTemplateRenderer:
    @classmethod
    def render(
        cls,
        template_path: Path,
        output_path: Path,
        replacements: dict[str, str],
    ) -> None:
        with (
            ZipFile(template_path, "r") as source,
            ZipFile(
                output_path,
                "w",
                compression=ZIP_DEFLATED,
            ) as target,
        ):
            for name in source.namelist():
                content = source.read(name)

                if name.endswith(".xml"):
                    text = content.decode("utf-8")

                    for placeholder, value in replacements.items():
                        text = text.replace(
                            placeholder,
                            value,
                        )

                    content = text.encode("utf-8")

                target.writestr(
                    name,
                    content,
                )
