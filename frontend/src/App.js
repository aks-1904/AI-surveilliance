import React from "react";
import Dashboard from "./pages/Dashboard";
import "./App.css";
import GuardNotifications from "./components/GuardNotification";

function App() {
  return (
    <div className="App">
      <div className="mt-10">
        <GuardNotifications />
      </div>
      <Dashboard />
    </div>
  );
}

export default App;
