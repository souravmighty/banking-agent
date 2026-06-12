"use client";

import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { User, Check, X, AlertCircle } from "lucide-react";

interface UserIdInputProps {
  currentUserId: string;
  onUserIdChange: (userId: string) => void;
  onUserIdConfirm: (userId: string) => void;
  isLoading?: boolean;
  className?: string;
}

export function UserIdInput({
  currentUserId,
  onUserIdChange,
  onUserIdConfirm,
  isLoading = false,
  className = "",
}: UserIdInputProps): React.JSX.Element {
  const [inputValue, setInputValue] = useState<string>(currentUserId);
  const [isValid, setIsValid] = useState<boolean>(true);
  const [validationMessage, setValidationMessage] = useState<string>("");
  const [isEditing, setIsEditing] = useState<boolean>(!currentUserId);
  const [shouldShowValidation, setShouldShowValidation] =
    useState<boolean>(false);

  // Validate email format for the user field
  const validateUserId = (
    userId: string
  ): { valid: boolean; message: string } => {
    if (!userId.trim()) {
      return { valid: false, message: "Email ID is required" };
    }

    // Strict email validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userId.trim())) {
      return {
        valid: false,
        message: "Please enter a valid email address",
      };
    }

    return { valid: true, message: "" };
  };

  // Handle input changes WITHOUT validation during typing
  const handleInputChange = (value: string): void => {
    setInputValue(value);
    // Don't call onUserIdChange here - only call it when user confirms

    // Reset validation state during typing
    setShouldShowValidation(false);
    setIsValid(true);
    setValidationMessage("");
  };

  // Handle input blur - validate when they leave the field
  const handleInputBlur = (): void => {
    if (inputValue.trim()) {
      const validation = validateUserId(inputValue);
      setIsValid(validation.valid);
      setValidationMessage(validation.message);
      setShouldShowValidation(true);
    }
  };

  // Handle confirm button click
  const handleConfirm = (): void => {
    const validation = validateUserId(inputValue);
    setIsValid(validation.valid);
    setValidationMessage(validation.message);
    setShouldShowValidation(true);

    if (validation.valid) {
      onUserIdChange(inputValue); // Only call this when confirming
      onUserIdConfirm(inputValue);
      setIsEditing(false);
      setShouldShowValidation(false);
    }
  };

  // Handle edit button click
  const handleEdit = (): void => {
    setIsEditing(true);
    setInputValue(currentUserId);
    setShouldShowValidation(false);
    setIsValid(true);
    setValidationMessage("");
  };

  // Handle cancel button click
  const handleCancel = (): void => {
    setInputValue(currentUserId);
    setIsEditing(false);
    setShouldShowValidation(false);
    setIsValid(true);
    setValidationMessage("");
  };

  // Handle enter key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter" && isValid && inputValue.trim()) {
      handleConfirm();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  // Auto-focus input when editing starts
  useEffect(() => {
    if (isEditing) {
      const input = document.querySelector(
        'input[data-testid="user-id-input"]'
      ) as HTMLInputElement;
      if (input) {
        input.focus();
        input.select();
      }
    }
  }, [isEditing]);

  return (
    <div className={`${className}`}>
      {isEditing ? (
        <div className="bg-slate-700/50 backdrop-blur-sm border border-slate-600/50 rounded-lg p-2 flex items-center gap-2">
          <User className="w-4 h-4 text-slate-300 flex-shrink-0" />
          <Input
            data-testid="user-id-input"
            value={inputValue}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              handleInputChange(e.target.value)
            }
            onKeyDown={handleKeyPress}
            onBlur={handleInputBlur}
            type="email"
            inputMode="email"
            autoComplete="email"
            placeholder="Enter email ID"
            className={`w-32 text-xs bg-[#1a1f71] text-white border-[#4a509a] placeholder:text-[#c8cadf] focus:border-[#f0a500] focus:ring-[#f0a500]/20 ${
              !isValid ? "border-red-400" : ""
            }`}
            disabled={isLoading}
          />
          <Button
            size="sm"
            onClick={handleConfirm}
            disabled={
              !inputValue.trim() ||
              isLoading ||
              (shouldShowValidation && !isValid)
            }
            className="h-7 px-2 bg-[#f0a500] hover:bg-[#e19d00] text-[#1a1f71]"
          >
            {isLoading ? (
              <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <Check className="w-3 h-3" />
            )}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleCancel}
            disabled={isLoading}
            className="h-7 px-2 border-[#4a509a] text-[#c8cadf] hover:bg-white/6 hover:text-white"
          >
            <X className="w-3 h-3" />
          </Button>
          {shouldShowValidation && !isValid && validationMessage && (
            <div className="flex items-center gap-1 text-xs text-red-400">
              <AlertCircle className="w-3 h-3" />
              <span className="whitespace-nowrap">{validationMessage}</span>
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-[11px] uppercase tracking-[0.08em] text-[#c8cadf]">Email</span>
          <Badge
            variant="secondary"
            className="font-mono bg-[#f0a500] text-[#1a1f71] border-transparent hover:bg-[#e19d00]"
          >
            {currentUserId}
          </Badge>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleEdit}
            disabled={isLoading}
            className="text-[11px] h-6 px-2 text-[#c8cadf] hover:text-white hover:bg-white/6"
          >
            Edit
          </Button>
        </div>
      )}
    </div>
  );
}
