function detect_multilogin() {
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

  var features = policyFeatures();
  if (!features || features.length < 40) {
    return false;
  }

  function has(name) {
    return features.indexOf(name) >= 0;
  }

  if (has("ch-viewport-height")) {
    return false;
  }
  if (!has("hid") || !has("usb") || !has("xr-spatial-tracking")) {
    return false;
  }
  if (has("bluetooth")) {
    return false;
  }
  return true;
}

if (typeof window !== "undefined") {
  window.detect_multilogin = detect_multilogin;
}
