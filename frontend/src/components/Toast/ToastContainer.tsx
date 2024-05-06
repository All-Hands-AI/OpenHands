import React from 'react';
import { createPortal } from 'react-dom';

interface ToastProps {
    message: string;
    onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ message, onClose }) => {
    React.useEffect(() => {
        const timer = setTimeout(onClose, 3000); // Toast disappears after 3 seconds
        return () => clearTimeout(timer);
    }, [onClose]);  // Attach onClose dependency to reinitialize timer if onClose changes
    
    return createPortal(
        <div className="fixed bottom-10 right-10 bg-blue-600 text-white p-3 rounded shadow-lg">
            {message}
        </div>,
        document.body  // Render the toast into the body
    );
};

export default Toast;
