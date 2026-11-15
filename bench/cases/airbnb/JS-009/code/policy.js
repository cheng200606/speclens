// bad: multiline blocks without braces
export function applyPolicy(user, rules) {
  if (user.isAdmin)
    for (const rule of rules)
      user.policies.push(rule.id);
  return user;
}
