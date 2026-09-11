/* Task 12: safe mini-markdown formatter shared by all dream UIs.
 * Escapes HTML first, then renders **bold** and #-headings.
 * Both /dreams/ and the homepage quick-dream widget must use this
 * (same input -> same output).
 */
function formatInterpretation(text) {
  var escaped = String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
  return escaped
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^#{1,6}\s*(.+)$/gm, '<strong>$1</strong>');
}
