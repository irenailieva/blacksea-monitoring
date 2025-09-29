import { useState, useEffect } from "react";

export default function BackendTest() {
    const [message, setMessage] = useState("Loading...");

    useEffect(() => {
        fetch("http://127.0.0.1:8000/")
        .then((res) => res.json())
        .then((data) => setMessage(data.message))
        .catch((err) => setMessage("Error: " + err.message));
    }, []);

    return (
        <div className="p-6 text-xl font-semibold text-blue-600">
            Backend says: {message}
        </div>
    );
}
