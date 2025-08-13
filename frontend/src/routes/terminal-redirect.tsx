import { Navigate, useParams } from "react-router";

export default function TerminalRedirect() {
  const { conversationId } = useParams();
  return <Navigate to={`/conversations/${conversationId}`} replace />;
}
