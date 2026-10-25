import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";

import VehicleForm from "../components/VehicleForm";
import { apiRequest } from "../api/client";

vi.mock("../api/client", () => ({
  apiRequest: vi.fn(),
}));

beforeEach(() => {
  vi.resetAllMocks();
});

function renderForm(overrides = {}) {
  const props = {
    vehicle: null,
    onSaved: vi.fn(),
    onCancel: vi.fn(),
    onUnauthorized: vi.fn(),
    ...overrides,
  };

  render(<VehicleForm {...props} />);

  return props;
}

function fillVehicle() {
  for (const [label, value] of [
    ["Make", "Toyota"],
    ["Model", "Camry"],
    ["Category", "Sedan"],
    ["Price (USD)", "25000.50"],
    ["Quantity", "3"],
  ]) {
    fireEvent.change(screen.getByLabelText(label), {
      target: { value },
    });
  }
}

it("creates a vehicle with a decimal-string price", async () => {
  apiRequest.mockResolvedValueOnce({ id: "vehicle-1" });

  const props = renderForm();
  fillVehicle();

  fireEvent.click(
    screen.getByRole("button", { name: "Save vehicle" }),
  );

  await waitFor(() => {
    expect(props.onSaved).toHaveBeenCalled();
  });

  expect(apiRequest).toHaveBeenCalledWith("/vehicles", {
    method: "POST",
    body: {
      make: "Toyota",
      model: "Camry",
      category: "Sedan",
      price: "25000.50",
      quantity: 3,
    },
  });
});

it("updates an existing vehicle using PUT", async () => {
  apiRequest.mockResolvedValueOnce({ id: "vehicle-1" });

  const props = renderForm({
    vehicle: {
      id: "vehicle-1",
      make: "Toyota",
      model: "Camry",
      category: "Sedan",
      price: "25000.50",
      quantity: 3,
    },
  });

  fireEvent.change(screen.getByLabelText("Model"), {
    target: { value: "Corolla" },
  });

  fireEvent.click(
    screen.getByRole("button", { name: "Save vehicle" }),
  );

  await waitFor(() => {
    expect(props.onSaved).toHaveBeenCalled();
  });

  expect(apiRequest).toHaveBeenCalledWith(
    "/vehicles/vehicle-1",
    {
      method: "PUT",
      body: {
        make: "Toyota",
        model: "Corolla",
        category: "Sedan",
        price: "25000.50",
        quantity: 3,
      },
    },
  );
});

it("handles an expired session", async () => {
  const error = new Error("Authentication expired");
  error.status = 401;

  apiRequest.mockRejectedValueOnce(error);

  const props = renderForm();
  fillVehicle();

  fireEvent.click(
    screen.getByRole("button", { name: "Save vehicle" }),
  );

  await waitFor(() => {
    expect(props.onUnauthorized).toHaveBeenCalled();
  });

  expect(props.onSaved).not.toHaveBeenCalled();
});