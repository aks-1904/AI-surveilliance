import React, { useState, useEffect } from "react";
import useSocket from "../hooks/useSocket";

const GuardNotifications = () => {
  const socket = useSocket();
  const [notifications, setNotifications] = useState([]);
  const [permission, setPermission] = useState(Notification.permission);

  // Function to explicitly ask for permission via a button click
  const requestNotificationPermission = () => {
    if (!("Notification" in window)) {
      alert("This browser does not support desktop notification");
      return;
    }
    Notification.requestPermission().then((perm) => {
      setPermission(perm);
    });
  };

  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }

  useEffect(() => {
    if (!socket || typeof socket.on !== "function") return;

    socket.on("alert_updated", (updatedAlert) => {
      const guardNotes = updatedAlert.guard_notes || [];
      const latestNote = guardNotes[guardNotes.length - 1];

      if (latestNote && latestNote.sender !== "System") {
        // 1. Trigger OS-level notification if permitted
        if (permission === "granted") {
          new Notification(`Guard Update: ${latestNote.sender}`, {
            body: latestNote.message,
            icon: "/logo192.png", // Make sure this path matches your public folder
          });
        }

        // 2. Trigger the React Toast Overlay
        const newNotif = {
          id: Date.now(),
          sender: latestNote.sender,
          message: latestNote.message,
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };

        setNotifications((prev) => [newNotif, ...prev].slice(0, 3));

        setTimeout(() => {
          setNotifications((prev) => prev.filter((n) => n.id !== newNotif.id));
        }, 6000);
      }
    });

    return () => {
      if (typeof socket.off === "function") socket.off("alert_updated");
    };
  }, [socket, permission]);

  return (
    <>
      {permission === "default" && (
        <div className="fixed top-0 left-0 right-0 bg-blue-600 text-white text-center py-2 z-50 text-sm">
          Want OS-level alerts?
          <button
            onClick={requestNotificationPermission}
            className="ml-4 bg-white text-blue-600 font-bold px-3 py-1 rounded text-xs"
          >
            Enable notification
          </button>
        </div>
      )}
      {notifications.length > 0 && (
        <div className="fixed top-4 right-4 z-50 flex flex-col gap-3 w-80">
          {notifications.map((notif) => (
            <div
              key={notif.id}
              className="bg-gray-900 border-l-4 border-blue-500 text-white p-4 rounded-lg shadow-2xl flex items-start justify-between animate-fade-in-down"
            >
              <div className="flex gap-3">
                <div className="bg-blue-500/20 p-2 rounded-full h-10 w-10 flex items-center justify-center text-xl flex-shrink-0">
                  👮
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-blue-400">
                      {notif.sender}
                    </span>
                    <span className="text-xs text-gray-400">{notif.time}</span>
                  </div>
                  <p className="text-sm mt-1 text-gray-200">{notif.message}</p>
                </div>
              </div>
              <button
                onClick={() => dismissNotification(notif.id)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  );
};

export default GuardNotifications;
