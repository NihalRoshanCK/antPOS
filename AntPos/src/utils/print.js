// Opens Frappe's print view for a Sales Invoice.
//
// Replaces two copies of a hand-built URL that (a) spanned two lines, so a
// newline and indentation leaked into the query string, (b) sent
// format=undefined when the profile had no print format, (c) asked Frappe to
// hide the letterhead precisely when the profile named one, and (d) took the
// host from a server call that strips "www.", which can point at a different
// origin than the POS is running on.
export function openInvoicePrint(name, profile = {}) {
  if (!name || profile?.skip_printview) return null

  const params = new URLSearchParams({
    doctype: 'Sales Invoice',
    name,
    trigger_print: '1',
  })
  if (profile.print_format) params.set('format', profile.print_format)
  if (profile.letter_head) {
    params.set('letterhead', profile.letter_head)
    params.set('no_letterhead', '0')
  }

  return window.open(`${window.location.origin}/printview?${params}`, '_blank')
}
