# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pdf2zh-next==2.9.0", "babeldoc==0.6.2", "pymupdf==1.25.2", "bitstring==4.4.0"]
# ///
"""Translate English PDFs into left-English/right-Chinese reading copies."""

import argparse
import asyncio
import logging
import os
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path

import pymupdf
from pdf2zh_next import PDFSettings, SettingsModel, TranslationSettings
from pdf2zh_next import do_translate_async_stream
from pdf2zh_next.config.translate_engine_model import SiliconFlowFreeSettings


def source_pages(path):
    if path.suffix.lower() != ".pdf" or not path.is_file():
        raise ValueError(f"需要本地 PDF 文件：{path}")
    with pymupdf.open(path) as document:
        if not document.is_pdf or document.needs_pass or not document.page_count:
            raise ValueError(f"PDF 为空、无效或需要密码：{path}")
        if not any(page.get_text().strip() for page in document):
            raise ValueError(f"PDF 缺少可提取文字，请先生成 OCR 文字层：{path}")
        return [(page.rect.width, page.rect.height) for page in document]


def validate_output(path, dimensions):
    with pymupdf.open(path) as document:
        if not document.is_pdf or document.page_count != len(dimensions):
            raise ValueError("双语 PDF 页数与原文不一致")
        for page, (width, height) in zip(document, dimensions):
            if abs(page.rect.width / width - 2) > .06 or abs(page.rect.height / height - 1) > .06:
                raise ValueError(f"第 {page.number + 1} 页未生成左右并排版式")
        translated_text = any(
            any('\u3400' <= char <= '\u9fff' for char in page.get_text(
                clip=pymupdf.Rect(page.rect.width / 2, 0, page.rect.width, page.rect.height)
            ))
            for page in document
        )
        if not translated_text:
            raise ValueError("译文侧未找到可提取的中文内容")


async def translate_one(source, destination, dimensions):
    # Use explicit API settings, independently of the machine's CLI defaults.
    with tempfile.TemporaryDirectory(prefix=".pdf2zh-", dir=destination.parent) as output:
        settings = SettingsModel(
            translation=TranslationSettings(
                lang_in="en", lang_out="zh-CN", output=output,
                qps=4, pool_max_workers=4, no_auto_extract_glossary=True,
            ),
            pdf=PDFSettings(
                no_mono=True, watermark_output_mode="no_watermark",
                translate_table_text=True, disable_rich_text_translate=True,
            ),
            translate_engine_settings=SiliconFlowFreeSettings(),
        )
        async for event in do_translate_async_stream(settings, source):
            if event["type"] == "error":
                raise RuntimeError(event.get("error", "PDF2zh-Next 翻译失败"))
            if event["type"] == "finish":
                result = event["translate_result"].dual_pdf_path
                if result is None:
                    break
                validate_output(result, dimensions)
                # The temporary file and destination share a filesystem. An
                # exclusive link publishes the complete PDF without overwriting.
                os.link(result, destination)
                return
        raise RuntimeError("PDF2zh-Next 未返回双语 PDF")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", metavar="PDF", nargs="*", type=Path)
    parser.add_argument("-o", "--output-dir", metavar="DIR", type=Path)
    parser.add_argument("--check-toolchain", action="store_true", help="检查运行环境和依赖版本")
    args = parser.parse_args()
    if args.check_toolchain:
        if args.pdfs or args.output_dir:
            parser.error("--check-toolchain 请单独运行")
        dependencies = ("pdf2zh-next", "babeldoc", "pymupdf", "bitstring")
        versions = ", ".join(f"{name} {version(name)}" for name in dependencies)
        print(f"工具链可用：Python {platform.python_version()}, {versions}")
        return 0
    if not args.pdfs:
        parser.error("请提供至少一个 PDF 文件，或使用 --check-toolchain 检查工具链")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    jobs = []
    destinations = set()
    try:
        for path in args.pdfs:
            source = path.resolve()
            directory = args.output_dir.resolve() if args.output_dir else source.parent
            destination = directory / f"{source.stem}_中英对照.pdf"
            name_key = str(destination).casefold()
            if name_key in destinations:
                raise ValueError(f"多个输入对应同一输出文件，请分开运行：{destination}")
            destinations.add(name_key)
            jobs.append((source, destination, source_pages(source)))
    except Exception as exc:
        parser.error(str(exc))

    failed = False
    for source, destination, dimensions in jobs:
        try:
            if destination.exists():
                validate_output(destination, dimensions)
                print(f"已存在 {destination}", flush=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            print(f"正在翻译 {source.name}（{len(dimensions)} 页）", flush=True)
            asyncio.run(translate_one(source, destination, dimensions))
            print(f"已生成 {destination}", flush=True)
        except Exception as exc:
            failed = True
            print(f"处理失败 {source.name}｜{exc}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
