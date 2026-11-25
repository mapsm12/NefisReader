"use strict";

const NEFIS_TEXT = {
  en: {
    names: {HSIGN:"Significant wave height", RTP:"Peak period", DIR:"Wave direction", XP:"X coordinate", YP:"Y coordinate", U1:"U1 velocity", V1:"V1 velocity"},
    shape:"raw shape", row:"Row", record:"Record", layer:"layer",
    scale:"Colour scale for this slice; synthetic data.", copied:"Copied", selected:"Text selected",
    unavailable:"Examples unavailable. You can download them from GitHub.",
  },
  es: {
    names: {HSIGN:"Altura significativa", RTP:"Período pico", DIR:"Dirección de oleaje", XP:"Coordenada X", YP:"Coordenada Y", U1:"Velocidad U1", V1:"Velocidad V1"},
    shape:"matriz cruda", row:"Fila", record:"Registro", layer:"capa",
    scale:"Escala del plano mostrado; datos sintéticos.", copied:"Copiado", selected:"Texto seleccionado",
    unavailable:"No se cargaron los ejemplos. Puedes descargarlos desde GitHub.",
  },
  id: {
    names: {HSIGN:"Tinggi gelombang signifikan", RTP:"Periode puncak", DIR:"Arah gelombang", XP:"Koordinat X", YP:"Koordinat Y", U1:"Kecepatan U1", V1:"Kecepatan V1"},
    shape:"dimensi asli", row:"Baris", record:"Rekaman", layer:"lapisan",
    scale:"Skala warna untuk irisan ini; data sintetis.", copied:"Disalin", selected:"Teks dipilih",
    unavailable:"Contoh tidak dapat dimuat. Unduh berkasnya dari GitHub.",
  },
  "zh-Hans": {
    names: {HSIGN:"有效波高", RTP:"峰值周期", DIR:"波向", XP:"X 坐标", YP:"Y 坐标", U1:"U1 流速", V1:"V1 流速"},
    shape:"原始维度", row:"行", record:"记录", layer:"层",
    scale:"色标对应当前切片，数据为合成示例。", copied:"已复制", selected:"已选择文本",
    unavailable:"未能加载示例。可从 GitHub 下载文件。",
  },
  ja: {
    names: {HSIGN:"有義波高", RTP:"ピーク周期", DIR:"波向", XP:"X 座標", YP:"Y 座標", U1:"U1 流速", V1:"V1 流速"},
    shape:"元の配列形状", row:"行", record:"レコード", layer:"層",
    scale:"表示中の断面のカラースケール。合成データです。", copied:"コピーしました", selected:"テキストを選択しました",
    unavailable:"使用例を読み込めませんでした。GitHub からファイルをダウンロードできます。",
  },
  "pt-BR": {
    names: {HSIGN:"Altura significativa das ondas", RTP:"Período de pico", DIR:"Direção das ondas", XP:"Coordenada X", YP:"Coordenada Y", U1:"Velocidade U1", V1:"Velocidade V1"},
    shape:"dimensões originais", row:"Linha", record:"Registro", layer:"camada",
    scale:"Escala de cores deste corte; dados sintéticos.", copied:"Copiado", selected:"Texto selecionado",
    unavailable:"Não foi possível carregar os exemplos. Você pode baixá-los no GitHub.",
  },
  nl: {
    names: {HSIGN:"Significante golfhoogte", RTP:"Piekperiode", DIR:"Golfrichting", XP:"X-coördinaat", YP:"Y-coördinaat", U1:"U1-stroomsnelheid", V1:"V1-stroomsnelheid"},
    shape:"oorspronkelijke dimensies", row:"Rij", record:"Record", layer:"laag",
    scale:"Kleurenschaal voor deze doorsnede; synthetische gegevens.", copied:"Gekopieerd", selected:"Tekst geselecteerd",
    unavailable:"De voorbeelden konden niet worden geladen. Je kunt ze downloaden op GitHub.",
  },
};
