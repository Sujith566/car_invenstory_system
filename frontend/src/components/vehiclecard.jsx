export default function VehicleCard({
  vehicle,
  busy,
  isAdmin,
  onPurchase,
  onEdit,
  onDelete,
  onRestock,
}) {
  const price = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(vehicle.price));

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
          {vehicle.category}
        </span>

        <span
          className={`text-sm ${
            vehicle.quantity === 0
              ? "text-red-600"
              : "text-slate-500"
          }`}
        >
          {vehicle.quantity} in stock
        </span>
      </div>

      <h2 className="mt-5 text-xl font-bold">
        {vehicle.make} {vehicle.model}
      </h2>

      <p className="mt-4 text-2xl font-semibold">{price}</p>

      <button
        type="button"
        disabled={busy || vehicle.quantity === 0}
        onClick={() => onPurchase(vehicle)}
        className="mt-6 w-full rounded-lg bg-emerald-700 p-3 font-semibold text-white hover:bg-emerald-800 disabled:opacity-40"
      >
        {vehicle.quantity === 0
          ? "Out of stock"
          : "Purchase one"}
      </button>

      {isAdmin && (
        <div className="mt-3 grid grid-cols-3 gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => onEdit(vehicle)}
            className="rounded-lg border border-slate-300 px-2 py-3 text-sm disabled:opacity-40"
          >
            Edit
          </button>

          <button
            type="button"
            disabled={busy}
            onClick={() => onRestock(vehicle)}
            className="rounded-lg border border-slate-300 px-2 py-3 text-sm disabled:opacity-40"
          >
            Restock
          </button>

          <button
            type="button"
            disabled={busy}
            onClick={() => onDelete(vehicle)}
            className="rounded-lg bg-red-50 px-2 py-3 text-sm text-red-700 disabled:opacity-40"
          >
            Delete
          </button>
        </div>
      )}
    </article>
  );
}