// good: object destructuring
export function renderProfile(user) {
  const { name, email, city } = user;

  return `${name} <${email}> (${city})`;
}
