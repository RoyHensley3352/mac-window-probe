function detect_gologin() {
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

  if (!has("aria-notify")) {
    return false;
  }
  if (has("ch-ua-high-entropy-values") || has("record-ad-auction-events")) {
    return false;
  }
  if (!has("hid") || !has("usb") || !has("xr-spatial-tracking")) {
    return false;
  }
  if (!has("ch-viewport-height") || has("bluetooth")) {
    return false;
  }
  return true;
}

if (typeof window !== "undefined") {
  window.detect_gologin = detect_gologin;
}
