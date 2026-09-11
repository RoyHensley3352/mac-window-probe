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
  if (features.length < 40 || features.indexOf("bluetooth") < 0) {
    return false;
  }

  try {
    return policy.allowsFeature("bluetooth") === true;
  } catch (err) {
    void err;
    return false;
  }
}

if (typeof window !== "undefined") {
  window.detect_octo = detect_octo;
}
