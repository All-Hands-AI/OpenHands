// Reo.dev tracking initialization
(function() {
  var e, t, n;
  e = "6bac7145b4ee6ec";
  t = function() {
    Reo.init({clientID: "6bac7145b4ee6ec"});
  };
  n = document.createElement("script");
  n.src = "https://static.reo.dev/" + e + "/reo.js";
  n.defer = true;
  n.onload = t;
  document.head.appendChild(n);
})();

