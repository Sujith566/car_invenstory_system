import { useEffect, useState } from "react";

import { apiRequest } from "../api/client";
import VehicleCard from "./VehicleCard";
import VehicleForm from "./VehicleForm";

const emptyFilters = {
  make: "",
  model: "",
  category: "",
  min_price: "",
  max_price: "",
};

const filterLabels = {
  make: "Make",
  model: "Model",
  category: "Category",
  min_price: "Minimum price",
  max_price: "Maximum price",
};

export default function Dashboard({ user, onLogout }) {
  const [vehicles, setVehicles] = useState([]);
  const [filters, setFilters] = useState({ ...emptyFilters });
  const [search, setSearch] = useState("");
  const [refresh, setRefresh] = useState(0);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [editor, setEditor] = useState(null);
  const [restockTarget, setRestockTarget] = useState(null);
  const [restockQuantity, setRestockQuantity] = useState("1");

  useEffect(() => {
    const controller = new AbortController();

    async function loadVehicles() {
      setLoading(true);
      setError("");

      try {
        const path = search
          ? `/vehicles/search?${search}`
          : "/vehicles";

        const result = await apiRequest(path, {
          signal: controller.signal,
        });

        if (!controller.signal.aborted) {
          setVehicles(result);
        }
      } catch (error) {
        if (controller.signal.aborted) return;

        if (error.status === 401) {
          onLogout();
          return;
        }

        setError(error.message);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadVehicles();

    return () => controller.abort();
  }, [search, refresh, onLogout]);

  function handleSearch(event) {
    event.preventDefault();

    const minimum = filters.min_price;
    const maximum = filters.max_price;

    if (
      minimum !== "" &&
      maximum !== "" &&
      Number(minimum) > Number(maximum)
    ) {
      setError("Minimum price cannot exceed maximum price.");
      return;
    }

    const parameters = new URLSearchParams();

    for (const [key, value] of Object.entries(filters)) {
      const trimmedValue = value.trim();

      if (trimmedValue !== "") {
        parameters.set(key, trimmedValue);
      }
    }

    setSearch(parameters.toString());
    setRefresh((previous) => previous + 1);
    setMessage("");
  }

  function resetSearch() {
    setFilters({ ...emptyFilters });
    setSearch("");
    setRefresh((previous) => previous + 1);
    setMessage("");
  }

  async function runAction(path, options, successMessage) {
    setBusy(true);
    setError("");
    setMessage("");

    try {
      await apiRequest(path, options);

      setMessage(successMessage);
      setRefresh((previous) => previous + 1);

      return true;
    } catch (error) {
      if (error.status === 401) {
        onLogout();
      } else {
        setError(error.message);

        if (error.status === 409 || error.status === 404) {
          setRefresh((previous) => previous + 1);
        }
      }

      return false;
    } finally {
      setBusy(false);
    }
  }

  async function purchaseVehicle(vehicle) {
    const confirmed = window.confirm(
      `Purchase one ${vehicle.make} ${vehicle.model}?`,
    );

    if (!confirmed) return;

    await runAction(
      `/vehicles/${vehicle.id}/purchase`,
      {
        method: "POST",
        body: { quantity: 1 },
      },
      "Purchase successful. Inventory updated.",
    );
  }

  async function deleteVehicle(vehicle) {
    const confirmed = window.confirm(
      `Permanently delete ${vehicle.make} ${vehicle.model}?`,
    );

    if (!confirmed) return;

    await runAction(
      `/vehicles/${vehicle.id}`,
      { method: "DELETE" },
      "Vehicle deleted.",
    );
  }

  function openEditor(vehicle = null) {
    setRestockTarget(null);
    setEditor({ vehicle });
    setError("");
    setMessage("");
  }

  function openRestock(vehicle) {
    setEditor(null);
    setRestockTarget(vehicle);
    setRestockQuantity("1");
    setError("");
    setMessage("");
  }

  async function handleRestock(event) {
    event.preventDefault();

    const quantity = Number(restockQuantity);

    if (
      !Number.isInteger(quantity) ||
      quantity < 1 ||
      quantity > 1000000
    ) {
      setError("Enter a whole quantity between 1 and 1,000,000.");
      return;
    }

    const success = await runAction(
      `/vehicles/${restockTarget.id}/restock`,
      {
        method: "POST",
        body: { quantity },
      },
      "Vehicle restocked successfully.",
    );

    if (success) {
      setRestockTarget(null);
    }
  }

  const controlsDisabled =
    busy ||
    loading ||
    editor !== null ||
    restockTarget !== null;

  return (
    <main className="mx-auto max-w-6xl p-4 sm:p-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-700">
            Car dealership
          </p>

          <h1 className="mt-2 text-3xl font-bold">
            Vehicle inventory
          </h1>

          <p className="mt-2 break-all text-sm text-slate-500">
            {user.email} ·{" "}
            {user.is_admin ? "Administrator" : "Member"}
          </p>
        </div>

        <div className="flex gap-3">
          {user.is_admin && (
            <button
              type="button"
              disabled={controlsDisabled}
              onClick={() => openEditor()}
              className="rounded-lg bg-emerald-700 px-4 py-2 text-white disabled:opacity-40"
            >
              Add vehicle
            </button>
          )}

          <button
            type="button"
            onClick={onLogout}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2"
          >
            Sign out
          </button>
        </div>
      </header>

      {user.is_admin && editor && (
        <VehicleForm
          key={editor.vehicle?.id ?? "new"}
          vehicle={editor.vehicle}
          onUnauthorized={onLogout}
          onCancel={() => setEditor(null)}
          onSaved={() => {
            const wasCreating = !editor.vehicle;

            setEditor(null);
            setError("");
            setMessage("Vehicle saved successfully.");

            if (wasCreating) {
              setFilters({ ...emptyFilters });
              setSearch("");
            }

            setRefresh((previous) => previous + 1);
          }}
        />
      )}

      {user.is_admin && restockTarget && (
        <section className="mt-6 rounded-xl border border-emerald-200 bg-white p-6">
          <h2 className="text-xl font-bold">
            Restock {restockTarget.make} {restockTarget.model}
          </h2>

          <form onSubmit={handleRestock} className="mt-4">
            <fieldset disabled={busy}>
              <label className="block text-sm font-medium">
                Units to add
                <input
                  type="number"
                  min="1"
                  max="1000000"
                  step="1"
                  required
                  value={restockQuantity}
                  onChange={(event) =>
                    setRestockQuantity(event.target.value)
                  }
                  className="mt-2 block w-full max-w-xs rounded-lg border border-slate-300 p-3"
                />
              </label>

              <div className="mt-4 flex gap-3">
                <button
                  type="submit"
                  className="rounded-lg bg-emerald-700 px-5 py-3 text-white disabled:opacity-50"
                >
                  {busy ? "Updating..." : "Add stock"}
                </button>

                <button
                  type="button"
                  onClick={() => setRestockTarget(null)}
                  className="rounded-lg border border-slate-300 px-5 py-3"
                >
                  Cancel
                </button>
              </div>
            </fieldset>
          </form>
        </section>
      )}

      <form
        onSubmit={handleSearch}
        className="mt-8 grid gap-4 rounded-xl bg-white p-5 shadow-sm sm:grid-cols-2 lg:grid-cols-5"
      >
        {Object.keys(emptyFilters).map((key) => {
          const isPrice = key.includes("price");

          return (
            <label key={key} className="text-sm font-medium">
              {filterLabels[key]}

              <input
                type={isPrice ? "number" : "text"}
                min={isPrice ? "0" : undefined}
                max={isPrice ? "999999999.99" : undefined}
                step={isPrice ? "0.01" : undefined}
                maxLength={
                  isPrice ? undefined : key === "category" ? 60 : 100
                }
                value={filters[key]}
                onChange={(event) =>
                  setFilters((previous) => ({
                    ...previous,
                    [key]: event.target.value,
                  }))
                }
                className="mt-2 w-full rounded-lg border border-slate-300 p-2"
              />
            </label>
          );
        })}

        <div className="flex gap-3 sm:col-span-2 lg:col-span-5">
          <button
            type="submit"
            disabled={controlsDisabled}
            className="rounded-lg bg-slate-900 px-5 py-2 text-white disabled:opacity-40"
          >
            Search
          </button>

          <button
            type="button"
            disabled={controlsDisabled}
            onClick={resetSearch}
            className="rounded-lg border border-slate-300 px-5 py-2 disabled:opacity-40"
          >
            Reset
          </button>
        </div>
      </form>

      {error && (
        <p
          role="alert"
          className="mt-5 rounded-lg bg-red-50 p-4 text-red-700"
        >
          {error}
        </p>
      )}

      {message && (
        <p
          role="status"
          className="mt-5 rounded-lg bg-emerald-50 p-4 text-emerald-800"
        >
          {message}
        </p>
      )}

      {loading ? (
        <p role="status" className="mt-8">
          Loading vehicles...
        </p>
      ) : vehicles.length === 0 ? (
        <section className="mt-8 rounded-xl bg-white p-10 text-center">
          <h2 className="text-xl font-semibold">
            No vehicles to display
          </h2>

          <p className="mt-2 text-slate-500">
            {error
              ? "Resolve the error above and reload inventory."
              : "Try different filters or add your first vehicle."}
          </p>
        </section>
      ) : (
        <>
          <p className="mt-8 text-sm text-slate-500">
            {vehicles.length} vehicle records
          </p>

          <section className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {vehicles.map((vehicle) => (
              <VehicleCard
                key={vehicle.id}
                vehicle={vehicle}
                busy={controlsDisabled}
                isAdmin={user.is_admin}
                onPurchase={purchaseVehicle}
                onEdit={openEditor}
                onDelete={deleteVehicle}
                onRestock={openRestock}
              />
            ))}
          </section>
        </>
      )}
    </main>
  );
}