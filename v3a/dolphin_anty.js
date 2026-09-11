function detect_dolphin_anty() {
  function unmaskedPair() {
    var canvas = null;
    var gl = null;
    try {
      canvas = document.createElement("canvas");
      canvas.width = 8;
      canvas.height = 8;
      gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    } catch (err) {
      void err;
      return null;
    }
    if (!gl) {
      return null;
    }
    var info = null;
    try {
      info = gl.getExtension("WEBGL_debug_renderer_info");
    } catch (err) {
      void err;
      return null;
    }
    if (!info) {
      return null;
    }
    try {
      return {
        vendor: gl.getParameter(info.UNMASKED_VENDOR_WEBGL),
        renderer: gl.getParameter(info.UNMASKED_RENDERER_WEBGL),
      };
    } catch (err) {
      void err;
      return null;
    }
  }

  var pair = unmaskedPair();
  if (!pair) {
    return false;
  }
  if (typeof pair.vendor !== "string" || typeof pair.renderer !== "string") {
    return false;
  }
  return pair.vendor === "Google Inc." && pair.renderer === "ANGLE";
}

if (typeof window !== "undefined") {
  window.detect_dolphin_anty = detect_dolphin_anty;
}
