function detect_octo() {
  var policy = null;
  try {
    policy = document.featurePolicy || document.permissionsPolicy;
  } catch (err) {
    void err;
    return false;
  }
  if (!policy || typeof policy.features !== "function" ||
      typeof policy.allowsFeature !== "function") {
    return false;
  }

  var features = [];
  try {
    features = policy.features();
  } catch (err) {
    void err;
    return false;
  }
  if (features.length < 40) {
    return false;
  }
  if (features.indexOf("bluetooth") < 0 || features.indexOf("unload") < 0) {
    return false;
  }

  try {
    if (policy.allowsFeature("bluetooth") !== true) {
      return false;
    }
    return policy.allowsFeature("unload") === false;
  } catch (err) {
    void err;
    return false;
  }
}

if (typeof window !== "undefined") {
  window.detect_octo = detect_octo;
}
