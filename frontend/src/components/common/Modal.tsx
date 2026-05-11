import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import React from "react";

/**
 * @purpose Props for the Modal component.
 * @owner Gemini
 */
interface ModalProps {
  /**
   * Controls the visibility of the modal.
   */
  isOpen: boolean;
  /**
   * Callback function triggered when the modal requests to be closed.
   */
  onClose: () => void;
  /**
   * The title displayed at the top of the modal.
   */
  title: string;
  /**
   * The content to be rendered inside the modal body.
   */
  children: React.ReactNode;
}

/**
 * @purpose A wrapper around shadcn Dialog for displaying modal content.
 * Provides a title, controls visibility, and handles close actions.
 * @param {ModalProps} props - The props for the Modal component.
 * @returns {JSX.Element} The rendered Modal component.
 * @owner Gemini
 */
const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        {children}
      </DialogContent>
    </Dialog>
  );
};

export { Modal };