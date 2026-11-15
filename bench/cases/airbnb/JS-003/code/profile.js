// bad: repeated property access
export function renderProfile(user) {
  const name = user.name;
  const email = user.email;
  const city = user.city;

  return `${name} <${email}> (${city})`;
}
