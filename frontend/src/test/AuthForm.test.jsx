import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";

import AuthForm from "../components/AuthForm";
import {
  apiRequest,
  setAccessToken,
} from "../api/client";

vi.mock("../api/client", () => ({
  apiRequest: vi.fn(),
  setAccessToken: vi.fn(),
}));

beforeEach(() => {
  vi.resetAllMocks();
});

function fillCredentials() {
  fireEvent.change(screen.getByLabelText("Email address"), {
    target: { value: "user@example.com" },
  });

  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "StrongPassword123!" },
  });
}

it("logs in and loads the signed-in user", async () => {
  const user = {
    id: "user-1",
    email: "user@example.com",
    is_admin: false,
  };

  apiRequest
    .mockResolvedValueOnce({ access_token: "test-token" })
    .mockResolvedValueOnce(user);

  const onLogin = vi.fn();

  render(<AuthForm onLogin={onLogin} />);
  fillCredentials();

  fireEvent.click(
    screen.getByRole("button", { name: "Sign in" }),
  );

  await waitFor(() => {
    expect(onLogin).toHaveBeenCalledWith(user);
  });

  expect(apiRequest).toHaveBeenNthCalledWith(
    1,
    "/auth/login",
    {
      method: "POST",
      body: {
        email: "user@example.com",
        password: "StrongPassword123!",
      },
    },
  );

  expect(setAccessToken).toHaveBeenCalledWith("test-token");
  expect(apiRequest).toHaveBeenNthCalledWith(2, "/auth/me");
});

it("registers before logging in", async () => {
  apiRequest
    .mockResolvedValueOnce({ id: "user-1" })
    .mockResolvedValueOnce({ access_token: "test-token" })
    .mockResolvedValueOnce({
      id: "user-1",
      email: "user@example.com",
      is_admin: false,
    });

  const onLogin = vi.fn();

  render(<AuthForm onLogin={onLogin} />);

  fireEvent.click(
    screen.getByRole("button", {
      name: "New here? Create an account",
    }),
  );

  fillCredentials();

  fireEvent.click(
    screen.getByRole("button", { name: "Create account" }),
  );

  await waitFor(() => {
    expect(onLogin).toHaveBeenCalled();
  });

  expect(apiRequest.mock.calls.map(([path]) => path)).toEqual([
    "/auth/register",
    "/auth/login",
    "/auth/me",
  ]);
});

it("shows a login error without signing in", async () => {
  apiRequest.mockRejectedValueOnce(
    new Error("Invalid email or password"),
  );

  const onLogin = vi.fn();

  render(<AuthForm onLogin={onLogin} />);
  fillCredentials();

  fireEvent.click(
    screen.getByRole("button", { name: "Sign in" }),
  );

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Invalid email or password",
  );

  expect(onLogin).not.toHaveBeenCalled();
  expect(setAccessToken).toHaveBeenCalledWith("");
});