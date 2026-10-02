import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import { DesktopFallbackModal } from "./DesktopFallbackModal";

describe("DesktopFallbackModal", () => {
  it("does not render when isOpen is false", () => {
    render(
      <DesktopFallbackModal
        isOpen={false}
        onClose={vi.fn()}
        onRetry={vi.fn()}
      />
    );

    expect(screen.queryByTestId("desktop-fallback-modal")).not.toBeInTheDocument();
  });

  it("renders download links and instructions when isOpen is true", () => {
    const onClose = vi.fn();
    const onRetry = vi.fn();

    render(
      <DesktopFallbackModal
        isOpen={true}
        onClose={onClose}
        onRetry={onRetry}
      />
    );

    expect(screen.getByTestId("desktop-fallback-modal")).toBeInTheDocument();
    expect(screen.getByText("Launching Interview Ready Desktop")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /windows/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /macos/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /linux/i })).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    const onRetry = vi.fn();

    render(
      <DesktopFallbackModal
        isOpen={true}
        onClose={onClose}
        onRetry={onRetry}
      />
    );

    const closeBtn = screen.getByLabelText(/close dialog/i);
    fireEvent.click(closeBtn);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onRetry when retry button is clicked", () => {
    const onClose = vi.fn();
    const onRetry = vi.fn();

    render(
      <DesktopFallbackModal
        isOpen={true}
        onClose={onClose}
        onRetry={onRetry}
      />
    );

    const retryBtn = screen.getByTestId("retry-launch-btn");
    fireEvent.click(retryBtn);

    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
