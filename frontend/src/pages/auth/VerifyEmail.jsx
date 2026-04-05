import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { auth } from "../../services/api";
import { AlertCircle, Loader2, CheckCircle } from "lucide-react";

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const [status, setStatus] = useState("loading"); // loading, success, error
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus("error");
        setMessage("Invalid verification link");
        return;
      }

      try {
        await auth.verifyEmail({ token });
        setStatus("success");
        setMessage("Email verified successfully!");
      } catch (err) {
        setStatus("error");
        setMessage(err?.response?.data?.message || "Verification failed");
      }
    };

    verifyEmail();
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
      <div className="w-full max-w-[400px] bg-white rounded-2xl shadow-xl p-7 border border-gray-100">
        <div className="flex flex-col items-center">
          {status === "loading" && (
            <>
              <Loader2 size={48} className="text-blue-500 animate-spin mb-4" />
              <h2 className="text-2xl font-bold text-gray-900">Verifying...</h2>
              <p className="text-center text-gray-500 mt-2">
                Please wait while we verify your email.
              </p>
            </>
          )}

          {status === "success" && (
            <>
              <CheckCircle size={48} className="text-green-500 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900">Email Verified!</h2>
              <p className="text-center text-gray-500 mt-2">{message}</p>
              <button
                onClick={() => navigate("/signin")}
                className="mt-6 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 font-medium"
              >
                Sign In
              </button>
            </>
          )}

          {status === "error" && (
            <>
              <AlertCircle size={48} className="text-red-500 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900">Verification Failed</h2>
              <p className="text-center text-gray-500 mt-2">{message}</p>
              <button
                onClick={() => navigate("/signin")}
                className="mt-6 text-blue-600 hover:underline font-medium"
              >
                Back to Sign In
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;