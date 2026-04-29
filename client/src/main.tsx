import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import App from "./App";
import ReturnForm from "./pages/ReturnForm";
import ClaimStatus from "./pages/ClaimStatus";
import AdminDashboard from "./pages/AdminDashboard";
import DemoPanel from "./pages/DemoPanel";
import BillingVerification from "./pages/BillingVerification";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Navigate to="/return" replace />} />
          <Route path="return" element={<ReturnForm />} />
          <Route path="status/:claimId" element={<ClaimStatus />} />
          <Route path="admin" element={<AdminDashboard />} />
          <Route path="demo" element={<DemoPanel />} />
          <Route path="billing" element={<BillingVerification />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
