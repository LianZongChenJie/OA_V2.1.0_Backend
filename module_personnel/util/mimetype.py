IMAGE_MIMETYPES = {
    # 常见图片格式
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'jpe': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'bmp': 'image/bmp',
    'webp': 'image/webp',
    'svg': 'image/svg+xml',
    'ico': 'image/x-icon',
    'tif': 'image/tiff',
    'tiff': 'image/tiff',

    # 其他图片格式
    'heic': 'image/heic',
    'heif': 'image/heif',
    'avif': 'image/avif',
    'jp2': 'image/jp2',
    'jpx': 'image/jpx',
    'jpm': 'image/jpm',
    'jxr': 'image/jxr',
}

DOCUMENT_MIMETYPES = {
    # PDF
    'pdf': 'application/pdf',

    # Word 文档
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'dot': 'application/msword',
    'dotx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template',

    # Excel 表格
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xlt': 'application/vnd.ms-excel',
    'xltx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
    'xlsb': 'application/vnd.ms-excel.sheet.binary.macroEnabled.12',
    'xlsm': 'application/vnd.ms-excel.sheet.macroEnabled.12',

    # PowerPoint 演示文稿
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'pot': 'application/vnd.ms-powerpoint',
    'potx': 'application/vnd.openxmlformats-officedocument.presentationml.template',
    'pps': 'application/vnd.ms-powerpoint',
    'ppsx': 'application/vnd.openxmlformats-officedocument.presentationml.slideshow',

    # 文本文件
    'txt': 'text/plain',
    'text': 'text/plain',
    'log': 'text/plain',
    'md': 'text/markdown',
    'markdown': 'text/markdown',
    'rtf': 'application/rtf',

    # 其他文档
    'odt': 'application/vnd.oasis.opendocument.text',
    'ods': 'application/vnd.oasis.opendocument.spreadsheet',
    'odp': 'application/vnd.oasis.opendocument.presentation',
    'odg': 'application/vnd.oasis.opendocument.graphics',
    'epub': 'application/epub+zip',
    'mobi': 'application/x-mobipocket-ebook',
    'azw': 'application/vnd.amazon.ebook',

    # 压缩文件
    'zip': 'application/zip',
    'rar': 'application/vnd.rar',
    '7z': 'application/x-7z-compressed',
    'tar': 'application/x-tar',
    'gz': 'application/gzip',
    'bz2': 'application/x-bzip2',
    'xz': 'application/x-xz',
}

VIDEO_MIMETYPES = {
    # 常见视频格式
    'mp4': 'video/mp4',
    'mpeg': 'video/mpeg',
    'mpg': 'video/mpeg',
    'm4v': 'video/x-m4v',
    'mov': 'video/quicktime',
    'qt': 'video/quicktime',
    'avi': 'video/x-msvideo',
    'wmv': 'video/x-ms-wmv',
    'asf': 'video/x-ms-asf',

    # Web 视频
    'webm': 'video/webm',
    'ogv': 'video/ogg',
    'ogg': 'video/ogg',

    # 其他格式
    'flv': 'video/x-flv',
    'f4v': 'video/x-f4v',
    'mkv': 'video/x-matroska',
    'mts': 'video/mp2t',
    'ts': 'video/mp2t',
    'm2ts': 'video/mp2t',
    '3gp': 'video/3gpp',
    '3g2': 'video/3gpp2',
}

AUDIO_MIMETYPES = {
    # 常见音频格式
    'mp3': 'audio/mpeg',
    'mpeg': 'audio/mpeg',
    'mpga': 'audio/mpeg',

    # 无损格式
    'wav': 'audio/wav',
    'wave': 'audio/wav',
    'flac': 'audio/flac',
    'alac': 'audio/alac',
    'aiff': 'audio/aiff',
    'aif': 'audio/aiff',
    'aifc': 'audio/aiff',

    # 其他格式
    'ogg': 'audio/ogg',
    'oga': 'audio/ogg',
    'opus': 'audio/opus',
    'weba': 'audio/webm',
    'm4a': 'audio/mp4',
    'm4b': 'audio/mp4',
    'ac3': 'audio/ac3',
    'dts': 'audio/vnd.dts',
    'mid': 'audio/midi',
    'midi': 'audio/midi',
    'kar': 'audio/midi',
    'ra': 'audio/x-realaudio',
    'ram': 'audio/x-pn-realaudio',
}

APPLICATION_MIMETYPES = {
    # 代码文件
    'json': 'application/json',
    'xml': 'application/xml',
    'javascript': 'application/javascript',
    'js': 'application/javascript',
    'mjs': 'application/javascript',
    'ts': 'application/typescript',
    'wasm': 'application/wasm',

    # 可执行文件
    'exe': 'application/x-msdownload',
    'msi': 'application/x-msi',
    'bin': 'application/octet-stream',
    'dmg': 'application/x-apple-diskimage',
    'pkg': 'application/x-newton-compatible-pkg',
    'deb': 'application/x-debian-package',
    'rpm': 'application/x-rpm',

    # 字体文件
    'ttf': 'font/ttf',
    'otf': 'font/otf',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
    'eot': 'application/vnd.ms-fontobject',

    # 其他
    'csv': 'text/csv',
    'tsv': 'text/tab-separated-values',
    'ics': 'text/calendar',
    'ical': 'text/calendar',
    'vcf': 'text/vcard',
    'vcard': 'text/vcard',
}

MIMETYPES = {
    # 图片
    **IMAGE_MIMETYPES,

    # 文档
    **DOCUMENT_MIMETYPES,

    # 视频
    **VIDEO_MIMETYPES,

    # 音频
    **AUDIO_MIMETYPES,

    # 应用程序
    **APPLICATION_MIMETYPES,

    # 其他补充
    'html': 'text/html',
    'htm': 'text/html',
    'css': 'text/css',
    'less': 'text/css',
    'scss': 'text/css',
    'sass': 'text/css',
    'php': 'text/x-php',
    'py': 'text/x-python',
    'java': 'text/x-java-source',
    'c': 'text/x-c',
    'cpp': 'text/x-c++',
    'h': 'text/x-c',
    'hpp': 'text/x-c++',
    'go': 'text/x-go',
    'rb': 'text/x-ruby',
    'rs': 'text/x-rust',
    'swift': 'text/x-swift',
    'kt': 'text/x-kotlin',

    # 压缩文件补充
    'tgz': 'application/tar+gzip',
    'tar.gz': 'application/tar+gzip',
    'tar.bz2': 'application/tar+bzip2',
    'tar.xz': 'application/tar+xz',

    # 光盘镜像
    'iso': 'application/x-iso9660-image',
    'img': 'application/x-iso9660-image',

    # CAD 文件
    'dwg': 'application/x-dwg',
    'dxf': 'application/x-dxf',
    'dgn': 'application/x-dgn',

    # 3D 模型
    'stl': 'application/vnd.ms-pki.stl',
    'obj': 'text/plain',
    'fbx': 'application/octet-stream',
    'gltf': 'model/gltf+json',
    'glb': 'model/gltf-binary',
}
