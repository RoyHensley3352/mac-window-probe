function detect_headless() {
  function headlessUserAgent() {
    try {
      return navigator.userAgent.indexOf("HeadlessChrome") >= 0;
    } catch (err) {
      void err;
      return false;
    }
  }

  function noPointerDevice() {
    try {
      return window.matchMedia("(hover: none)").matches &&
        window.matchMedia("(pointer: none)").matches &&
        window.matchMedia("(any-pointer: none)").matches;
    } catch (err) {
      void err;
      return false;
    }
  }

  function framelessGeometry() {
    try {
      if (typeof window.outerWidth !== "number" ||
          typeof window.innerWidth !== "number") {
        return false;
      }
      if (window.outerWidth <= 0 || window.innerWidth <= 0) {
        return false;
      }
      if (window.outerWidth !== window.innerWidth) {
        return false;
      }
      return window.outerWidth < screen.width;
    } catch (err) {
      void err;
      return false;
    }
  }

  function framelessByPosition() {
    try {
      return window.screenY === 0 && framelessGeometry();
    } catch (err) {
      void err;
      return false;
    }
  }

  function defaultHeadlessScreen() {
    try {
      return screen.width === 800 && screen.height === 600 &&
        screen.availWidth === 800 && screen.availHeight === 600;
    } catch (err) {
      void err;
      return false;
    }
  }

  function productDetected(name) {
    try {
      var fn = window["detect_" + name];
      return typeof fn === "function" && fn() === true;
    } catch (err) {
      void err;
      return false;
    }
  }

  function anyProductDetected() {
    var names = ["ads_power", "dolphin_anty", "gologin", "multilogin", "octo"];
    for (var i = 0; i < names.length; i++) {
      if (productDetected(names[i])) {
        return true;
      }
    }
    return false;
  }

  if (headlessUserAgent()) {
    return true;
  }
  if (noPointerDevice()) {
    return true;
  }
  if (productDetected("octo")) {
    return framelessByPosition();
  }
  return anyProductDetected() && defaultHeadlessScreen();
}

if (typeof window !== "undefined") {
  window.detect_headless = detect_headless;
}
