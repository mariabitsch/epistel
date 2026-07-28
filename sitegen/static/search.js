/* epistel — filtering and searching the letter index, in the browser.
 *
 * The page is complete before this file runs: every letter is already in the
 * document, with the values it can be filtered by on the element itself. So
 * this script never builds markup and never writes data into the page as
 * HTML. It does exactly three things:
 *
 *   1. takes `hidden` off the controls, which is why a reader without
 *      JavaScript is never shown a filter that would do nothing;
 *   2. hides and unhides the rows that are already there;
 *   3. writes two numbers, as text, into the status line.
 *
 * The free-text index (assets/search-index.js, ~370 kB) is fetched the first
 * time somebody actually searches. Browsing and the three facets need none of
 * it, and most readers are browsing.
 *
 * Folding must agree with `sitegen/search.py`: lower case, æ→ae, ø→oe, å→aa,
 * then decorations dropped. Change it in one place and you have broken the
 * other.
 */
(function () {
  "use strict";

  var form = document.getElementById("finder");
  if (!form || !("hidden" in document.createElement("div"))) {
    return;
  }

  var MINIMUM_TOKEN = 2;
  var DEBOUNCE_MS = 120;

  var query = document.getElementById("finder-query");
  var selects = {
    sender: document.getElementById("finder-afsender"),
    recipient: document.getElementById("finder-modtager"),
    year: document.getElementById("finder-aar")
  };
  var countOut = form.querySelector(".finder-count");
  var termsOut = form.querySelector(".finder-terms");
  var empty = document.getElementById("finder-empty");

  var entries = [].map.call(
    document.querySelectorAll(".letter-entry"),
    function (element) {
      return {
        element: element,
        slug: element.getAttribute("data-slug"),
        sender: element.getAttribute("data-sender") || "",
        recipient: element.getAttribute("data-recipient") || "",
        year: element.getAttribute("data-year") || ""
      };
    }
  );
  if (!entries.length) {
    return;
  }

  var groups = [].slice.call(document.querySelectorAll(".correspondence"));
  var volumes = [].slice.call(document.querySelectorAll(".volume"));
  var volumeLinks = {};
  [].forEach.call(document.querySelectorAll(".volume-list a"), function (link) {
    volumeLinks[link.getAttribute("href").slice(1)] = link.parentNode;
  });

  /* ---------------------------------------------------------------- folding */

  function fold(value) {
    return value
      .toLowerCase()
      .replace(/æ/g, "ae")
      .replace(/ø/g, "oe")
      .replace(/å/g, "aa")
      .replace(/ä/g, "ae")
      .replace(/ö/g, "oe")
      .replace(/ü/g, "ue")
      .replace(/ß/g, "ss")
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function terms(value) {
    var words = fold(value).match(/[0-9a-z]+/g) || [];
    return words.filter(function (word) {
      return word.length >= MINIMUM_TOKEN;
    });
  }

  /* ------------------------------------------------------------ the index */

  var index = null;
  var indexState = "absent";
  var pending = false;

  function loadIndex() {
    if (indexState !== "absent") {
      return;
    }
    indexState = "loading";
    var script = document.createElement("script");
    script.src = "assets/search-index.js";
    script.onload = function () {
      index = window.epistelSearchIndex || null;
      indexState = index ? "ready" : "failed";
      if (pending) {
        pending = false;
        apply();
      }
    };
    script.onerror = function () {
      /* No index, no free-text search. The facets keep working, and the
         status line stops claiming a search happened. */
      indexState = "failed";
      if (pending) {
        pending = false;
        apply();
      }
    };
    document.head.appendChild(script);
  }

  /* Every letter holding this word, by position in index.letters. Words that
     merely contain it count too, so "kierkeg" finds "Kierkegaards" — the
     corpus is 19th century Danish and inflects everything. */
  function positionsFor(word) {
    var words = index.words;
    var found = Object.create(null);
    var name;
    for (name in words) {
      if (name === word || name.indexOf(word) !== -1) {
        words[name].forEach(function (position) {
          found[position] = true;
        });
      }
    }
    return found;
  }

  function matchingSlugs(wanted) {
    var slugs = null;
    wanted.forEach(function (word) {
      var positions = positionsFor(word);
      var here = Object.create(null);
      Object.keys(positions).forEach(function (position) {
        var slug = index.letters[position];
        if (slug && (slugs === null || slugs[slug])) {
          here[slug] = true;
        }
      });
      slugs = here;
    });
    return slugs;
  }

  /* ----------------------------------------------------------- filtering */

  function apply() {
    var wanted = terms(query.value);
    var slugs = null;

    if (wanted.length) {
      if (indexState === "ready") {
        slugs = matchingSlugs(wanted);
      } else if (indexState === "failed") {
        wanted = [];
      } else {
        pending = true;
        loadIndex();
        return;
      }
    }

    var shown = 0;
    entries.forEach(function (entry) {
      var visible =
        matches(selects.sender, entry.sender) &&
        matches(selects.recipient, entry.recipient) &&
        matches(selects.year, entry.year) &&
        (slugs === null || Boolean(slugs[entry.slug]));
      entry.element.hidden = !visible;
      if (visible) {
        shown += 1;
      }
    });

    groups.forEach(hideWhenEmpty);
    volumes.forEach(function (volume) {
      var link = volumeLinks[volume.id];
      hideWhenEmpty(volume);
      if (link) {
        link.hidden = volume.hidden;
      }
    });

    report(shown, wanted);
  }

  function matches(select, value) {
    return !select || !select.value || select.value === value;
  }

  function hideWhenEmpty(section) {
    section.hidden = !section.querySelector(".letter-entry:not([hidden])");
  }

  /* The status line quotes the reader back to themselves — what they typed,
     not what the folding made of it. Nobody searched for "snustobaksdaase". */
  function report(shown, wanted) {
    var typed = query.value.trim();
    countOut.textContent = shown === 1 ? "1 brev" : shown + " breve";
    if (indexState === "failed" && typed) {
      termsOut.textContent = " — søgeindekset kunne ikke hentes; filtrene virker stadig";
    } else if (wanted.length) {
      termsOut.textContent = " med \u00bb" + typed + "\u00ab";
    } else if (typed) {
      termsOut.textContent = " \u2014 et s\u00f8geord skal v\u00e6re p\u00e5 mindst to tegn";
    } else {
      termsOut.textContent = "";
    }
    empty.hidden = shown !== 0;
  }

  /* --------------------------------------------------------------- wiring */

  var timer = null;
  function schedule() {
    window.clearTimeout(timer);
    timer = window.setTimeout(apply, DEBOUNCE_MS);
  }

  query.addEventListener("input", schedule);
  query.addEventListener("focus", loadIndex, { once: true });
  Object.keys(selects).forEach(function (name) {
    if (selects[name]) {
      selects[name].addEventListener("change", apply);
    }
  });
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    window.clearTimeout(timer);
    apply();
  });
  form.addEventListener("reset", function () {
    /* The form clears itself after this handler, so re-read it afterwards. */
    window.setTimeout(apply, 0);
  });

  form.hidden = false;
  apply();
})();
