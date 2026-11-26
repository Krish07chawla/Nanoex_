// Small helpers to show money, percentages and times.

export const money = (n) => {
  const value = Number(n ?? 0);
  const text = Math.abs(value).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return (value < 0 ? "-₹" : "₹") + text;
};

export const percent = (n) => `${n > 0 ? "+" : ""}${Number(n ?? 0).toFixed(2)}%`;

// "green" for profit, "red" for loss, "" for zero
export const pnlClass = (n) => (n > 0 ? "green" : n < 0 ? "red" : "");

// The server sends UTC times. Add "Z" when it is missing so the browser knows.
export const toDate = (iso) => new Date(/[zZ]$|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + "Z");

export const clockText = (ms) =>
  new Date(ms).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

export const dateTimeText = (iso) =>
  iso ? toDate(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "-";
