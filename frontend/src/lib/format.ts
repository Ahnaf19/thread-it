// Money formatting lives on the frontend (ADR-0001): the API returns an integer
// in whole Taka, we render the ৳ symbol + thousands separators.
export function formatTaka(amount: number): string {
  return `৳${amount.toLocaleString("en-US")}`;
}
