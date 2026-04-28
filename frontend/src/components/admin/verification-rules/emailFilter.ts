type EmailOption = {
  message_id: string;
  subject?: string | null;
  from_email?: string | null;
  verification_code?: string | null;
};

export function filterVerificationTestEmails<T extends EmailOption>(emails: T[], query: string): T[] {
  const keyword = query.trim().toLowerCase();
  if (!keyword) return emails;

  return emails.filter((email) => {
    const haystacks = [
      email.message_id,
      email.subject || "",
      email.from_email || "",
      email.verification_code || "",
    ];
    return haystacks.some((value) => value.toLowerCase().includes(keyword));
  });
}

export function sortVerificationTestEmails<T extends EmailOption>(emails: T[], onlyWithCode: boolean = false): T[] {
  const next = onlyWithCode ? emails.filter((email) => !!email.verification_code) : [...emails];
  return next.sort((left, right) => Number(!!right.verification_code) - Number(!!left.verification_code));
}
