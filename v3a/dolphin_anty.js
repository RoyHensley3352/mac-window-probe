function detect_dolphin_anty() {
  function policyFeatures() {
    var policy = null;
    try {
      policy = document.featurePolicy || document.permissionsPolicy;
    } catch (err) {
      void err;
      return null;
    }
    if (!policy || typeof policy.features !== "function") {
      return null;
    }
    try {
      return policy.features();
    } catch (err) {
      void err;
      return null;
    }
  }

  function coreCount() {
    try {
      var n = navigator.hardwareConcurrency;
      return typeof n === "number" ? n : -1;
    } catch (err) {
      void err;
      return -1;
    }
  }

  function memoryGib() {
    try {
      var m = navigator.deviceMemory;
      return typeof m === "number" ? m : -1;
    } catch (err) {
      void err;
      return -1;
    }
  }

  var features = policyFeatures();
  if (!features || features.length < 40) {
    return false;
  }

  function has(name) {
    return features.indexOf(name) >= 0;
  }

  if (has("attribution-reporting")) {
    return false;
  }
  if (!has("shared-storage") || !has("ch-viewport-height")) {
    return false;
  }
  if (!has("hid") || !has("usb") || !has("xr-spatial-tracking")) {
    return false;
  }
  if (has("bluetooth")) {
    return false;
  }

  var cores = coreCount();
  var mem = memoryGib();
  if (cores < 1 || cores > 4) {
    return false;
  }
  if (mem < 1 || mem > 8) {
    return false;
  }
  return true;
}

if (typeof window !== "undefined") {
  window.detect_dolphin_anty = detect_dolphin_anty;
}
