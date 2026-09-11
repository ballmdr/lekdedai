/* Task 28: privacy-first analytics — ไม่ส่งข้อความฝัน/เลข/IP, ไม่ใช้ cookie.
 * - session id สุ่มเก็บใน localStorage (ไม่ผูกตัวตน)
 * - ผู้ใช้ opt-out ได้ผ่าน localStorage lekdedai_analytics_optout = "1" หรือ Do Not Track
 * - payload มีแค่ {name, session_id} เท่านั้น
 */
(function () {
  var ID_KEY = 'lekdedai_analytics_id';
  var OPT_OUT_KEY = 'lekdedai_analytics_optout';

  function isOptedOut() {
    try {
      if (localStorage.getItem(OPT_OUT_KEY) === '1') return true;
    } catch (e) { /* private mode */ }
    if (navigator.doNotTrack === '1' || window.doNotTrack === '1') return true;
    return false;
  }

  function sessionId() {
    try {
      var id = localStorage.getItem(ID_KEY);
      if (!id) {
        id = '';
        var chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        for (var i = 0; i < 16; i++) {
          id += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        localStorage.setItem(ID_KEY, id);
      }
      return id;
    } catch (e) {
      return '';
    }
  }

  function getCookie(name) {
    var cookies = document.cookie ? document.cookie.split(';') : [];
    for (var i = 0; i < cookies.length; i++) {
      var c = cookies[i].trim();
      if (c.substring(0, name.length + 1) === name + '=') {
        return decodeURIComponent(c.substring(name.length + 1));
      }
    }
    return null;
  }

  function track(name) {
    if (isOptedOut()) return;
    var id = sessionId();
    if (!id) return;
    var body = JSON.stringify({ name: name, session_id: id });
    try {
      fetch('/analytics/event/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') || ''
        },
        body: body,
        keepalive: true
      });
    } catch (e) { /* ล้มเงียบ ไม่กระทบ UX */ }
  }

  window.LekAnalytics = { track: track, optedOut: isOptedOut };

  document.addEventListener('DOMContentLoaded', function () {
    var root = document.body;
    if (!root) return;
    if (root.getAttribute('data-analytics-view')) {
      track(root.getAttribute('data-analytics-view'));
    }
  });
})();
