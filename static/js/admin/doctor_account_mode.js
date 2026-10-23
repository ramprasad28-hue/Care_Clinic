/**
 * DoctorAdmin add form: toggles between the two account modes.
 *
 * "Select existing user"  -> show the user picker, hide/disabled the
 *                            provisioned-account fields.
 * "Create new doctor account" -> show the account fields, hide the picker.
 *
 * Inputs are disabled when their rows are hidden so stale values are not
 * submitted; the server remains the authoritative gatekeeper either way,
 * so with JavaScript unavailable the extra rows are simply always visible
 * and mode validation happens server-side.
 */
(function () {
  "use strict";

  var NEW_FIELD_CLASSES = [
    "field-new_first_name",
    "field-new_last_name",
    "field-new_email",
    "field-new_phone",
    "field-new_password1",
    "field-new_password2",
  ];
  var EXISTING_FIELD_CLASSES = ["field-user"];

  function waitFor(selector, callback) {
    var el = document.querySelector(selector);
    if (el) {
      callback(el);
      return;
    }
    // The admin inserts heavy widgets (autocompletes, inlines) after
    // DOMContentLoaded in some configurations; retry briefly.
    var attempts = 0;
    var timer = setInterval(function () {
      var found = document.querySelector(selector);
      if (found || attempts > 20) {
        clearInterval(timer);
        if (found) {
          callback(found);
        }
      }
      attempts += 1;
    }, 50);
  }

  function toggleField(selector, visible) {
    document.querySelectorAll(selector).forEach(function (row) {
      row.hidden = !visible;
      row.querySelectorAll("input, select, textarea, button").forEach(
        function (el) {
          el.disabled = !visible;
        }
      );
      // Hide trigger/filter chrome that renders outside the input.
      row.querySelectorAll(".related-widget-wrapper-link").forEach(
        function (el) {
          el.classList.toggle("hidden", !visible);
          el.setAttribute("tabindex", visible ? "0" : "-1");
        }
      );
    });
  }

  function apply(modeEl) {
    var isNew = modeEl.value === "new";
    NEW_FIELD_CLASSES.forEach(function (cls) {
      toggleField("." + cls, isNew);
    });
    EXISTING_FIELD_CLASSES.forEach(function (cls) {
      toggleField("." + cls, !isNew);
    });
  }

  function init(modeEl) {
    apply(modeEl);
    modeEl.addEventListener("change", function () {
      apply(modeEl);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var modeEl = document.querySelector("[data-account-mode-selector]");
    if (modeEl) {
      init(modeEl);
      return;
    }
    // Autocomplete widgets can persist the select markup after hydration;
    // watch briefly for the marker to appear.
    waitFor("[data-account-mode-selector]", init);
  });
})();
