import { useCallback, useState } from "react";

import { setAccessToken } from "./api/client";
import AuthForm from "./components/AuthForm";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [user, setUser] = useState(null);

  const logout = useCallback(() => {
    setAccessToken("");
    setUser(null);
  }, []);

  if (!user) {
    return <AuthForm onLogin={setUser} />;
  }

  return (
    <Dashboard
      user={user}
      onLogout={logout}
    />
  );
}