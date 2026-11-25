"""Render localized static pages from the Spanish site source."""

import argparse
from pathlib import Path
import re


# Source HTML fragments, then English, Indonesian, and Simplified Chinese.
ROWS = """
Explora salidas Delft3D 4 en NEFIS y conviértelas a NetCDF con Python. Prueba ejemplos WAVE 2D y FLOW 3D.|Read Delft3D 4 NEFIS outputs and convert them to NetCDF with Python. Try WAVE 2D and FLOW 3D examples.|Baca keluaran NEFIS Delft3D 4 dan konversikan ke NetCDF dengan Python. Coba contoh WAVE 2D dan FLOW 3D.|使用 Python 读取 Delft3D 4 的 NEFIS 输出并转为 NetCDF。试用 WAVE 2D 和 FLOW 3D 示例。
Paquete Python para Delft3D 4|Python package for Delft3D 4|Paket Python untuk Delft3D 4|适用于 Delft3D 4 的 Python 软件包
Saltar al contenido|Skip to content|Lewati ke konten|跳转到内容
NefisReader, inicio|NefisReader home|Beranda NefisReader|NefisReader 首页
aria-label="Principal"|aria-label="Main navigation"|aria-label="Navigasi utama"|aria-label="主导航"
aria-label="Idioma"|aria-label="Language"|aria-label="Bahasa"|aria-label="语言"
>Ejemplos<|>Examples<|>Contoh<|>示例<
>Instalación<|>Install<|>Instalasi<|>安装<
PAQUETE PYTHON LIBRE · V0.1|OPEN-SOURCE PYTHON PACKAGE · V0.1|PAKET PYTHON SUMBER TERBUKA · V0.1|开源 PYTHON 软件包 · V0.1
Lee salidas NEFIS de Delft3D 4 y conviértelas a <strong>NetCDF</strong>. Incluye la herramienta <code>d3dnefis</code>, una API Python y un servidor MCP opcional.|Read Delft3D 4 NEFIS outputs and convert them to <strong>NetCDF</strong>. Includes the <code>d3dnefis</code> command, a Python API, and an optional MCP server.|Baca keluaran NEFIS Delft3D 4 dan konversikan ke <strong>NetCDF</strong>. Tersedia perintah <code>d3dnefis</code>, API Python, dan server MCP opsional.|读取 Delft3D 4 的 NEFIS 输出并转为 <strong>NetCDF</strong>。提供 <code>d3dnefis</code> 命令、Python API 和可选的 MCP 服务器。
Instalar en Linux|Install on Linux|Instal di Linux|在 Linux 上安装
Explorar ejemplos 2D y 3D|Explore 2D and 3D examples|Jelajahi contoh 2D dan 3D|浏览 2D 和 3D 示例
Flujo de trabajo: de NEFIS a Python y NetCDF|Workflow: NEFIS to Python and NetCDF|Alur kerja: dari NEFIS ke Python dan NetCDF|工作流程：从 NEFIS 到 Python 和 NetCDF
Un campo sobre una malla en tres capas, esquema conceptual|Conceptual diagram of a field on a three-layer grid|Skema konseptual medan pada kisi tiga lapis|三层网格上的场示意图
EJEMPLOS INTERACTIVOS|INTERACTIVE EXAMPLES|CONTOH INTERAKTIF|交互式示例
Explorador WAVE 2D y FLOW 3D.|Explore WAVE 2D and FLOW 3D.|Jelajahi WAVE 2D dan FLOW 3D.|浏览 WAVE 2D 和 FLOW 3D
Elige un campo de oleaje o una capa de velocidad. Los valores se exportaron con NefisReader a partir de los ejemplos sintéticos del repositorio.|Choose a wave field or a velocity layer. NefisReader exported these values from the repository's synthetic examples.|Pilih medan gelombang atau lapisan kecepatan. Nilai ini diekspor dengan NefisReader dari contoh sintetis di repositori.|请选择波浪场或流速层。这些数值由 NefisReader 从仓库中的合成示例导出。
>Ejemplo<|>Example<|>Contoh<|>示例<
WAVE · oleaje 2D|WAVE · 2D waves|WAVE · gelombang 2D|WAVE · 二维波浪
FLOW · velocidad 3D|FLOW · 3D velocity|FLOW · kecepatan 3D|FLOW · 三维流速
>Variable<|>Variable<|>Variabel<|>变量<
>Registro<|>Record<|>Rekaman<|>记录<
>Capa<|>Layer<|>Lapisan<|>层<
Archivos .dat y .def|.dat and .def files|Berkas .dat dan .def|.dat 和 .def 文件
Altura significativa|Significant wave height|Tinggi gelombang signifikan|有效波高
Cargando ejemplo…|Loading example…|Memuat contoh…|正在加载示例…
Descargar CSV|Download CSV|Unduh CSV|下载 CSV
Plano de valores de ejemplo|Sample values for one plane|Nilai contoh pada satu bidang|单层示例数值
Datos sintéticos; no son observaciones ni resultados de la tesis.|Synthetic data, not observations or thesis results.|Data sintetis, bukan pengamatan atau hasil tesis.|合成数据，非观测数据或论文结果。
Activa JavaScript o descarga las parejas para probar en Python.|Enable JavaScript or download the file pairs to try them in Python.|Aktifkan JavaScript atau unduh pasangan berkas untuk mencobanya di Python.|请启用 JavaScript，或下载文件对后在 Python 中试用。
El explorador visualiza cortes de ejemplo ya calculados. El paquete instalado lee y convierte tus propias parejas <code>.dat/.def</code>. La página no recibe archivos.|The explorer displays precomputed slices. The installed package reads and converts your own <code>.dat/.def</code> pairs. This page does not accept uploads.|Penjelajah menampilkan irisan yang sudah dihitung. Paket yang terpasang membaca dan mengonversi pasangan <code>.dat/.def</code> milik Anda. Halaman ini tidak menerima unggahan.|浏览器展示预先生成的切片。安装软件包后可读取、转换自己的 <code>.dat/.def</code> 文件对。本网页不接收文件上传。
Ver mapas generados a partir de un NetCDF exportado|See maps from an exported NetCDF|Lihat peta dari NetCDF hasil ekspor|查看用导出的 NetCDF 生成的地图
EJEMPLOS DE POSPROCESO|POST-PROCESSING EXAMPLES|CONTOH PASCAPROSES|后处理示例
Del NetCDF al mapa.|From NetCDF to maps.|Dari NetCDF ke peta.|从 NetCDF 到地图
NefisReader exporta los campos. Un script de Python los combina para dibujar mapas de oleaje. Ambos ejemplos usan la misma bahía sintética: no son simulaciones ni datos del Callao.|NefisReader exports the fields. A Python script combines them into maps. Both examples use the same synthetic bay, not a simulation or data from Callao.|NefisReader mengekspor medan, lalu skrip Python menggabungkannya menjadi peta. Kedua contoh memakai teluk sintetis yang sama, bukan hasil simulasi atau data Callao. Label gambar berbahasa Inggris.|NefisReader 导出各个变量场，再通过 Python 脚本绘制地图。两幅图使用同一合成海湾，并非数值模拟或卡亚俄实测数据。图内标注为英文。
Abrir mapa de batimetría y vectores a tamaño completo|Open full-size bathymetry and vector map|Buka peta batimetri dan vektor ukuran penuh|打开全尺寸水深和矢量图
Mapa sintético de profundidad: el azul se oscurece hacia aguas profundas y las flechas doradas muestran el transporte de energía alrededor de una isla.|Synthetic depth map: darker blue means deeper water, and gold arrows show energy transport around an island.|Peta kedalaman sintetis: biru lebih gelap menunjukkan air lebih dalam; panah emas menandai transpor energi di sekitar pulau.|合成水深图：蓝色越深表示水越深；金色箭头表示岛屿周围的能量输运。
Batimetría y flujo de energía|Bathymetry and energy flux|Batimetri dan fluks energi|水深与能量通量
Fondo: <code>DEPTH</code> en metros. Flechas: <code>TRANSP_X</code> y <code>TRANSP_Y</code> en kW/m. Solo se dibujan sobre agua.|Background: <code>DEPTH</code> in metres. Arrows: <code>TRANSP_X</code> and <code>TRANSP_Y</code> in kW/m, shown only over water.|Latar: <code>DEPTH</code> dalam meter. Panah: <code>TRANSP_X</code> dan <code>TRANSP_Y</code> dalam kW/m, hanya di atas air.|底图：<code>DEPTH</code>，单位米。箭头：<code>TRANSP_X</code> 和 <code>TRANSP_Y</code>，单位 kW/m，仅在水域绘制。
Descargar PNG|Download PNG|Unduh PNG|下载 PNG
Abrir mapa de altura significativa e isóbatas a tamaño completo|Open full-size wave-height and depth-contour map|Buka peta tinggi gelombang dan kontur kedalaman ukuran penuh|打开全尺寸有效波高及等深线图
Mapa sintético de altura significativa con isóbatas de 10, 20 y 40 metros y una franja de menor altura detrás de la isla.|Synthetic significant wave height map with 10, 20 and 40 metre depth contours and lower waves behind the island.|Peta tinggi gelombang signifikan sintetis dengan kontur kedalaman 10, 20, dan 40 meter serta gelombang lebih rendah di belakang pulau.|合成有效波高图包含 10、20 和 40 米等深线，岛后波高较低。
Altura significativa e isóbatas|Significant wave height and depth contours|Tinggi gelombang signifikan dan kontur kedalaman|有效波高与等深线
Colores: <code>HSIGN</code> en metros. Líneas: contornos de igual profundidad. El gris identifica tierra en el ejemplo sintético.|Colours: <code>HSIGN</code> in metres. Lines: depth contours. Grey marks land in the synthetic example.|Warna: <code>HSIGN</code> dalam meter. Garis: kontur kedalaman. Abu-abu menandai daratan pada contoh sintetis.|颜色表示 <code>HSIGN</code>（米），线条表示等深线。合成示例中的灰色区域为陆地。
Reproducir ambos mapas con Python|Reproduce both maps with Python|Reproduksi kedua peta dengan Python|使用 Python 复现两幅图
INSTALACIÓN|INSTALLATION|INSTALASI|安装
Instala el paquete y lee tus corridas.|Install the package and read your model outputs.|Instal paket dan baca keluaran model Anda.|安装软件包并读取模型输出
Linux x86-64, Python 3.9+ y conexión a internet para instalar dependencias.|Linux x86-64, Python 3.9+, and internet access to install dependencies.|Linux x86-64, Python 3.9+, dan akses internet untuk menginstal dependensi.|需要 Linux x86-64 和 Python 3.9+。安装依赖时需要联网。
Descarga el paquete|Download the package|Unduh paket|下载软件包
y ejecuta estos comandos desde la carpeta de descargas. No necesitas instalar Delft3D.|and run these commands from your downloads folder. You do not need to install Delft3D.|dan jalankan perintah berikut dari folder unduhan. Anda tidak perlu memasang Delft3D.|后，在下载目录中运行以下命令。无需安装 Delft3D。
>Copiar<|>Copy<|>Salin<|>复制<
¿Ya tienes un archivo?|Already have a file?|Sudah memiliki berkas?|已有输出文件？
Pasa un archivo <code>.dat</code> o la carpeta de la corrida a <code>d3dnefis</code>. Con <code>--inventory</code> puedes revisar las variables sin convertir.|Pass a <code>.dat</code> file or the run folder to <code>d3dnefis</code>. Use <code>--inventory</code> to list variables without converting.|Berikan berkas <code>.dat</code> atau folder keluaran kepada <code>d3dnefis</code>. Gunakan <code>--inventory</code> untuk melihat daftar variabel tanpa konversi.|将 <code>.dat</code> 文件或运行目录传给 <code>d3dnefis</code>。使用 <code>--inventory</code> 可查看变量而不进行转换。
Conecta tu agente por MCP|Connect your agent via MCP|Hubungkan agen Anda melalui MCP|通过 MCP 连接智能体
El servidor local inventaría y lee recortes de NEFIS o NetCDF en la carpeta autorizada. Requiere Python 3.10+.|The local server lists variables and reads slices from NEFIS or NetCDF files in the allowed folder. Requires Python 3.10+.|Server lokal menampilkan daftar variabel dan membaca irisan NEFIS atau NetCDF dalam folder yang diizinkan. Memerlukan Python 3.10+.|本地服务器可列出变量，并读取授权目录中 NEFIS 或 NetCDF 文件的切片。需要 Python 3.10+。
Guía MCP para Codex y otros clientes|MCP guide for Codex and other clients|Panduan MCP untuk Codex dan klien lain|面向 Codex 和其他客户端的 MCP 指南
CRÉDITOS Y ALCANCE|CREDITS AND SCOPE|KREDIT DAN CAKUPAN|致谢与适用范围
Software libre, con fuentes.|Open-source software.|Perangkat lunak sumber terbuka.|开源软件
es un proyecto independiente. No es un producto oficial de Deltares ni implica su respaldo.|is an independent project. It is not an official Deltares product or endorsed by Deltares.|adalah proyek independen. Ini bukan produk resmi dan tidak mewakili dukungan Deltares.|是一个独立项目，并非 Deltares 官方产品，也不代表得到其背书。
La biblioteca NEFIS corresponde a Deltares. Sus|Deltares develops the NEFIS library. Its|Deltares mengembangkan pustaka NEFIS. Arsip|NEFIS 库由 Deltares 开发。其
fuentes, avisos y pasos de compilación|source code, notices and build instructions|kode sumber, pemberitahuan, dan petunjuk kompilasi|源代码、声明和编译说明
se distribuyen por separado dentro del repositorio. Los ejemplos son sintéticos; no contienen datos de la tesis.|are distributed separately in the repository. Examples are synthetic and contain no thesis data.|didistribusikan terpisah di dalam repositori. Contoh bersifat sintetis dan tidak memuat data tesis.|在仓库中单独提供。示例为合成数据，不包含论文数据。
El código propio está bajo|The project's own code uses the|Kode proyek ini menggunakan|本项目自有代码采用
licencia MIT|MIT licence|lisensi MIT|MIT 许可证
La biblioteca NEFIS de Deltares conserva sus|The Deltares NEFIS library retains its|Pustaka NEFIS dari Deltares tetap mengikuti|Deltares 的 NEFIS 库保留其
avisos y licencia propios|own notices and licence|pemberitahuan dan lisensinya sendiri|原有的声明和许可证
¿Te sirvió NefisReader?|Was NefisReader useful?|Apakah NefisReader bermanfaat?|NefisReader 对你有帮助吗？
Dale una estrella en GitHub|Star on GitHub|Beri bintang di GitHub|在 GitHub 上点星
En el repositorio, inicia sesión y pulsa <strong>Star</strong> para guardarlo y apoyar el proyecto.|Sign in on GitHub and click <strong>Star</strong> to bookmark the repository and support the project.|Masuk ke GitHub lalu klik <strong>Star</strong> untuk menandai repositori dan mendukung proyek ini.|登录 GitHub 后，点击 <strong>Star</strong> 收藏仓库并支持项目。
Si quieres apoyar el proyecto con una donación voluntaria,|If you'd like to support the project with a voluntary donation,|Jika ingin mendukung proyek dengan donasi sukarela,|如果你愿意通过自愿捐赠支持项目，
¡contáctame!|get in touch!|hubungi saya!|欢迎联系我！
El enlace abre una consulta pública en GitHub. No compartas datos de pago.|This opens a public GitHub issue. Do not share payment details there.|Tautan membuka isu publik di GitHub. Jangan bagikan informasi pembayaran di sana.|链接会打开公开的 GitHub issue，请勿在那里发布付款信息。
Reportar un problema|Report an issue|Laporkan masalah|报告问题
""".strip()

LANGS = (("en", "index.html"), ("id", "id.html"), ("zh-Hans", "zh.html"))
EXTRA_LANGS = (("ja", "ja.html"), ("pt-BR", "pt.html"), ("nl", "nl.html"))


def extra_mappings(rows):
    english_to_source = {row[1]: row[0] for row in rows}
    source = Path(__file__).with_name("web_locales_extra.txt")
    maps = {lang: {} for lang, _ in EXTRA_LANGS}
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        key, *translations = line.split("|")
        matches = [key] if key in english_to_source else [
            fragment for fragment in english_to_source if fragment.startswith(key)
        ]
        if len(matches) != 1 or len(translations) != len(EXTRA_LANGS):
            raise ValueError(f"Ambiguous or malformed translation key: {key}")
        fragment = english_to_source[matches[0]]
        for (lang, _), translation in zip(EXTRA_LANGS, translations):
            if fragment in maps[lang] or not translation.strip():
                raise ValueError(f"Duplicate or empty translation for {lang}: {key}")
            maps[lang][fragment] = translation
    for lang, values in maps.items():
        if missing := set(english_to_source.values()) - values.keys():
            raise ValueError(f"Missing {lang} translations: {sorted(missing)}")
    return maps


def render(directory: Path) -> None:
    template = (directory / "es.html").read_text(encoding="utf-8")
    rows = [line.split("|") for line in ROWS.splitlines()]
    assert all(len(row) == 4 for row in rows)
    assert all(row[0] in template for row in rows), [row[0] for row in rows if row[0] not in template]
    pattern = re.compile("|".join(re.escape(row[0]) for row in sorted(rows, key=lambda row: -len(row[0]))))
    mappings = {lang: {row[0]: row[column] for row in rows}
                for column, (lang, _) in enumerate(LANGS, start=1)}
    mappings.update(extra_mappings(rows))
    for lang, filename in LANGS + EXTRA_LANGS:
        mapping = mappings[lang]
        html = pattern.sub(lambda match: mapping[match[0]], template)
        html = html.replace('<html lang="es">', f'<html lang="{lang}">', 1).replace(' aria-current="page"', '', 1)
        html = re.sub(rf'(<a [^>]+data-lang="{lang}"[^>]+)>', r'\1 aria-current="page">', html, count=1)
        html = html.replace('figures/batimetria_vectores.png', 'figures/bathymetry_vectors.png')
        html = html.replace('figures/altura_isobatas.png', 'figures/height_depth_contours.png')
        html = html.replace('examples/MAPAS_OLEAJE.md', 'README.en.md#reproduce-the-maps')
        html = html.replace('blob/main/MCP.md', 'blob/main/README.en.md#mcp')
        html = html.replace('Consulta%20sobre%20donaciones%20a%20NefisReader', 'NefisReader%20donation%20inquiry')
        (directory / filename).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    render(parser.parse_args().directory)
