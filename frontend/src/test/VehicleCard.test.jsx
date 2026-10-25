import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import VehicleCard from "../components/VehicleCard";

const vehicle = {
  id: "vehicle-1",
  make: "Toyota",
  model: "Camry",
  category: "Sedan",
  price: "25000.50",
  quantity: 3,
};

function renderCard(overrides = {}) {
  const props = {
    vehicle,
    busy: false,
    isAdmin: false,
    onPurchase: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onRestock: vi.fn(),
    ...overrides,
  };

  render(<VehicleCard {...props} />);

  return props;
}

describe("VehicleCard", () => {
  it("displays vehicle details", () => {
    renderCard();

    expect(screen.getByText("Toyota Camry")).toBeInTheDocument();
    expect(screen.getByText("Sedan")).toBeInTheDocument();
    expect(screen.getByText("$25,000.50")).toBeInTheDocument();
    expect(screen.getByText("3 in stock")).toBeInTheDocument();
  });

  it("passes the selected vehicle to the purchase handler", () => {
    const props = renderCard();

    fireEvent.click(
      screen.getByRole("button", { name: "Purchase one" }),
    );

    expect(props.onPurchase).toHaveBeenCalledWith(vehicle);
  });

  it("disables purchasing when stock is zero", () => {
    renderCard({
      vehicle: { ...vehicle, quantity: 0 },
    });

    expect(
      screen.getByRole("button", { name: "Out of stock" }),
    ).toBeDisabled();
  });

  it("hides management controls from regular members", () => {
    renderCard();

    for (const name of ["Edit", "Restock", "Delete"]) {
      expect(
        screen.queryByRole("button", { name }),
      ).not.toBeInTheDocument();
    }
  });

  it("connects administrator controls to their handlers", () => {
    const props = renderCard({ isAdmin: true });

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.click(screen.getByRole("button", { name: "Restock" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    expect(props.onEdit).toHaveBeenCalledWith(vehicle);
    expect(props.onRestock).toHaveBeenCalledWith(vehicle);
    expect(props.onDelete).toHaveBeenCalledWith(vehicle);
  });

  it("disables all card actions while busy", () => {
    renderCard({
      isAdmin: true,
      busy: true,
    });

    for (const button of screen.getAllByRole("button")) {
      expect(button).toBeDisabled();
    }
  });
});