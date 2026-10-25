import { useState } from "react";

import { apiRequest } from "../api/client";

export default function VehicleForm({
  vehicle,
  onSaved,
  onCancel,
  onUnauthorized,
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    const form = new FormData(event.currentTarget);

    const body = {
      make: form.get("make").trim(),
      model: form.get("model").trim(),
      category: form.get("category").trim(),
      price: form.get("price"),
      quantity: Number(form.get("quantity")),
    };

    setBusy(true);
    setError("");

    try {
      await apiRequest(
        vehicle ? `/vehicles/${vehicle.id}` : "/vehicles",
        {
          method: vehicle ? "PUT" : "POST",
          body,
        },
      );

      onSaved();
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }

      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mt-6 rounded-xl border border-emerald-200 bg-white p-6">
      <h2 className="text-xl font-bold">
        {vehicle ? "Edit vehicle" : "Add vehicle"}
      </h2>

      <form onSubmit={handleSubmit} className="mt-5">
        <fieldset
          disabled={busy}
          className="grid gap-4 sm:grid-cols-2"
        >
          {["make", "model", "category"].map((field) => (
            <label key={field} className="text-sm font-medium">
              {field.charAt(0).toUpperCase() + field.slice(1)}

              <input
                name={field}
                defaultValue={vehicle?.[field] ?? ""}
                required
                maxLength={field === "category" ? 60 : 100}
                className="mt-2 w-full rounded-lg border border-slate-300 p-3"
              />
            </label>
          ))}

          <label className="text-sm font-medium">
            Price (USD)
            <input
              name="price"
              type="number"
              min="0"
              max="999999999.99"
              step="0.01"
              defaultValue={vehicle?.price ?? ""}
              required
              className="mt-2 w-full rounded-lg border border-slate-300 p-3"
            />
          </label>

          <label className="text-sm font-medium">
            Quantity
            <input
              name="quantity"
              type="number"
              min="0"
              max="1000000"
              step="1"
              defaultValue={vehicle?.quantity ?? 0}
              required
              className="mt-2 w-full rounded-lg border border-slate-300 p-3"
            />
          </label>

          {error && (
            <p
              role="alert"
              className="rounded-lg bg-red-50 p-3 text-red-700 sm:col-span-2"
            >
              {error}
            </p>
          )}

          <div className="flex gap-3 sm:col-span-2">
            <button
              type="submit"
              className="rounded-lg bg-emerald-700 px-5 py-3 text-white disabled:opacity-50"
            >
              {busy ? "Saving..." : "Save vehicle"}
            </button>

            <button
              type="button"
              onClick={onCancel}
              className="rounded-lg border border-slate-300 px-5 py-3"
            >
              Cancel
            </button>
          </div>
        </fieldset>
      </form>
    </section>
  );
}