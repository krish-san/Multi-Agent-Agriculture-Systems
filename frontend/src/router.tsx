import { createBrowserRouter, RouterProvider } from "react-router-dom";
import AgentsPage from "./components/AgentsPage";
import Layout from "./components/Layout";
import DashboardPage from "./components/DashboardPage";
import WorkflowsPage from "./components/WorkflowsPage";
import ReportsPage from "./components/ReportsPage";
import StatisticsPage from "./components/StatisticsPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: "agents",
        element: <AgentsPage />,
      },
      {
        path: "workflows",
        element: <WorkflowsPage />,
      },
      {
        path: "reports",
        element: <ReportsPage />,
      },
      {
        path: "statistics",
        element: <StatisticsPage />,
      },
    ],
  },
]);

export function Router() {
  return <RouterProvider router={router} />;
}

export default router;
