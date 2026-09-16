// antPOS signs in through Frappe's own login page (password reset, two-factor
// and social logins included) and comes back to where the user was.
export function loginUrl(
  path = window.location.pathname + window.location.search,
) {
  return `/login?redirect-to=${encodeURIComponent(path)}`
}

export function redirectToLogin() {
  window.location.href = loginUrl()
}

// Frappe answers a request from an expired session with 403 and resets the
// user_id cookie to Guest.
export function sessionEnded(error) {
  if (error?.response?.status !== 403) return false
  const user = new URLSearchParams(document.cookie.split('; ').join('&')).get(
    'user_id',
  )
  return !user || user === 'Guest'
}

let redirecting = false

// Resource fetcher that sends the user to log in when their session has ended,
// instead of leaving every request failing on screen.
export function withLoginRedirect(fetcher) {
  return (options) =>
    fetcher(options).catch((error) => {
      if (!redirecting && sessionEnded(error)) {
        redirecting = true
        redirectToLogin()
      }
      throw error
    })
}
