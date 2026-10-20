/* Care_Clinic — small progressive enhancements.
   Everything here is optional: the site works fully without it. */
(function () {
    "use strict";

    /* --- Mobile navigation --------------------------------------- */
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("site-nav");

    if (toggle && nav) {
        var reduceMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

        var openNav = function () {
            nav.classList.remove("is-closing");
            nav.classList.add("is-open");
            toggle.setAttribute("aria-expanded", "true");
        };

        var closeNav = function () {
            if (!nav.classList.contains("is-open")) {
                return;
            }
            toggle.setAttribute("aria-expanded", "false");
            nav.classList.remove("is-open");
            if (reduceMotion) {
                nav.classList.remove("is-closing");
                return;
            }
            /* Keep the panel in flow just long enough to play the
               close animation, then drop it (see animationend below). */
            nav.classList.add("is-closing");
        };

        /* Clean up after the close animation finishes. */
        nav.addEventListener("animationend", function (event) {
            if (event.animationName === "nav-close") {
                nav.classList.remove("is-closing");
            }
        });

        toggle.addEventListener("click", function () {
            if (nav.classList.contains("is-open")) {
                closeNav();
            } else {
                openNav();
            }
        });

        /* Close after choosing a link in a collapsible drawer (the
           mobile drawer and the dense authenticated drawer). On wider
           desktop layouts the nav is permanently visible and is-open is
           false, making this a no-op. */
        nav.addEventListener("click", function (event) {
            if (
                event.target.closest("a") &&
                window.matchMedia("(max-width: 1180px)").matches
            ) {
                closeNav();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && nav.classList.contains("is-open")) {
                closeNav();
                toggle.focus();
            }
        });
    }

    /* --- Mega menus (Specialities + Doctors) ----------------------- */
    /* Click/keyboard first, plus pointer hover on desktop. The panels are
       labelled regions inside their nav LIs; Escape and outside clicks
       close them and focus returns to the trigger. Hover only engages
       with a real mouse at desktop widths, so touch/tap and the mobile
       drawer are never affected by it. Reduced motion never blocks the
       menu — it only skips animation (handled in CSS). */
    var megaMenus = [];

    /* Opening one mega menu closes any other that is still open. */
    function closeOtherMegas(current) {
        megaMenus.forEach(function (menu) {
            if (menu !== current && menu.isOpen()) {
                menu.setOpen(false);
            }
        });
    }

    document.querySelectorAll("[data-mega-trigger]").forEach(function (trigger) {
        var panel = document.getElementById(trigger.getAttribute("aria-controls"));
        if (!panel) {
            return;
        }

        /* The combined hover region is the LI: the panel lives inside it,
           so moving the pointer from the trigger into the panel never
           counts as "leaving". */
        var region = trigger.closest(".nav-mega") || trigger.parentElement;
        var desktop = window.matchMedia("(min-width: 901px)");
        var closeTimer = null;
        var pinned = false;

        var menu = {
            isOpen: function () {
                return trigger.getAttribute("aria-expanded") === "true";
            },
            setOpen: function (open) {
                if (open) {
                    closeOtherMegas(menu);
                }
                trigger.setAttribute("aria-expanded", open ? "true" : "false");
                panel.classList.toggle("is-open", open);
            },
            reset: function () {
                pinned = false;
                cancelClose();
                menu.setOpen(false);
            }
        };

        var cancelClose = function () {
            if (closeTimer) {
                window.clearTimeout(closeTimer);
                closeTimer = null;
            }
        };

        var scheduleClose = function () {
            cancelClose();
            closeTimer = window.setTimeout(function () {
                closeTimer = null;
                menu.setOpen(false);
            }, 260);
        };

        var isHover = function (event) {
            return event.pointerType === "mouse" && desktop.matches;
        };

        /* Click/keyboard (Enter or Space on the button also emits click):
           - from closed: opens the menu and pins it (stays open until the
             user closes it, even if the pointer drifts away);
           - while hover-open: pins it — this is why a click right after
             hovering never makes the panel vanish;
           - while pinned: closes it, like a normal toggle. */
        trigger.addEventListener("click", function () {
            cancelClose();
            if (!menu.isOpen()) {
                pinned = true;
                menu.setOpen(true);
            } else if (pinned) {
                pinned = false;
                menu.setOpen(false);
            } else {
                pinned = true;
                menu.setOpen(true);
            }
        });

        /* Hover: entering the trigger or panel opens it and cancels any
           pending close; leaving schedules a short, cancellable close so
           traversal through the header gap (and diagonal pointer paths)
           cannot flicker the panel open/shut. A pinned (clicked) menu
           ignores hover-out until the user closes it. */
        region.addEventListener("pointerenter", function (event) {
            if (isHover(event)) {
                cancelClose();
                if (!menu.isOpen()) {
                    menu.setOpen(true);
                }
            }
        });

        region.addEventListener("pointerleave", function (event) {
            if (isHover(event) && !pinned) {
                scheduleClose();
            }
        });

        /* Choosing a link in the desktop panel dismisses it; the drawer
           click handler above already closes the drawer on mobile. */
        panel.addEventListener("click", function (event) {
            if (
                event.target.closest("a") &&
                window.matchMedia("(min-width: 901px)").matches
            ) {
                menu.reset();
            }
        });

        document.addEventListener("click", function (event) {
            if (
                menu.isOpen() &&
                !trigger.contains(event.target) &&
                !panel.contains(event.target)
            ) {
                menu.reset();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && menu.isOpen()) {
                menu.reset();
                trigger.focus();
            }
        });

        megaMenus.push(menu);
    });

    /* --- Homepage: fixed dark navbar beyond the hero ----------------- */
    /* The transparent homepage header is absolute (out of flow); past the
       hero it switches to a fixed translucent surface, preserving overlap-
       free behaviour. No layout compensation is required in either state. */
    var heroHeader = document.querySelector(".site-header--hero");
    var heroSection = document.querySelector(".hero");
    if (heroHeader && heroSection) {
        var updateScrolled = function () {
            var threshold =
                heroSection.offsetHeight - heroHeader.offsetHeight;
            heroHeader.classList.toggle(
                "is-scrolled",
                window.scrollY > threshold
            );
        };
        window.addEventListener("scroll", updateScrolled, { passive: true });
        window.addEventListener("resize", updateScrolled);
        updateScrolled();
    }

    /* --- Auto-submit filter selects when JS is available --------- */
    document.querySelectorAll("[data-autosubmit]").forEach(function (control) {
        control.addEventListener("change", function () {
            if (control.form) {
                control.form.submit();
            }
        });
    });

    /* --- Confirmation for destructive / irreversible actions ----- */
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            var message = form.getAttribute("data-confirm") || "Are you sure?";
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    /* --- Guard against accidental double submissions ------------- */
    function reEnable() {
        document
            .querySelectorAll('form[data-guard] button[type="submit"]')
            .forEach(function (button) {
                button.disabled = false;
                if (button.dataset.originalLabel) {
                    button.textContent = button.dataset.originalLabel;
                }
            });
    }

    document.querySelectorAll("form[data-guard]").forEach(function (form) {
        form.addEventListener("submit", function () {
            var button = form.querySelector('button[type="submit"]');
            if (button && !button.disabled) {
                button.dataset.originalLabel = button.textContent;
                button.disabled = true;
                button.textContent = "Please wait\u2026";
            }
        });
    });

    window.addEventListener("pageshow", reEnable);

    /* --- Move focus to the first field error after a submit -------- */
    var firstError = document.querySelector(
        ".field--error input, .field--error select, .field--error textarea"
    );
    if (firstError) {
        firstError.focus();
    }

    /* --- One-shot section reveals --------------------------------- */
    /* Purely decorative: the content is already visible without this.
       Each element is revealed once when it scrolls into view, then
       stops being observed so it never replays. */
    var reveals = document.querySelectorAll(".reveal");
    if (reveals.length) {
        var showAll = function () {
            reveals.forEach(function (el) {
                el.classList.add("is-visible");
            });
        };

        if (
            window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
            !("IntersectionObserver" in window)
        ) {
            /* No animation wanted or possible — show everything now. */
            showAll();
        } else {
            var observer = new IntersectionObserver(
                function (entries) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            entry.target.classList.add("is-visible");
                            observer.unobserve(entry.target);
                        }
                    });
                },
                { rootMargin: "0px 0px -10% 0px", threshold: 0.05 }
            );

            reveals.forEach(function (el) {
                observer.observe(el);
            });

            /* Safety net: never leave content hidden if the observer
               somehow misses (e.g. it never fires). */
            window.setTimeout(function () {
                reveals.forEach(function (el) {
                    if (!el.classList.contains("is-visible")) {
                        var top = el.getBoundingClientRect().top;
                        if (top < window.innerHeight) {
                            el.classList.add("is-visible");
                        }
                    }
                });
            }, 2000);
        }
    }
})();

/* --- Booking summary: live "Time" line (separate scope; optional) ---
   Forms carrying data-slot-form (patient booking, reschedule,
   receptionist) show the chosen slot time in their summary strip.
   Without JS the summary still names doctor/date; "Not selected yet"
   is the fallback copy. */
(function () {
    "use strict";
    var slotForm = document.querySelector("form[data-slot-form]");
    if (!slotForm) {
        return;
    }
    var timeLine = slotForm.querySelector("[data-slot-summary-time]");
    var slots = slotForm.querySelectorAll(".slot-grid input[type=radio]");
    if (!timeLine || !slots.length) {
        return;
    }
    var syncTime = function () {
        var chosen = slotForm.querySelector(
            ".slot-grid input[type=radio]:checked"
        );
        if (chosen) {
            var label = chosen.closest(".slot-option");
            var text = label
                ? (label.querySelector(".slot-time") || {}).textContent
                : "";
            if (text) {
                timeLine.textContent = text.replace(/\s+/g, " ").trim();
                return;
            }
        }
        timeLine.textContent = "Not selected yet";
    };
    slots.forEach(function (radio) {
        radio.addEventListener("change", syncTime);
    });
    /* a back-navigation may restore a previously checked radio */
    window.addEventListener("pageshow", syncTime);
})();
