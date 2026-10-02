import type { Skill } from "@interview-ready/api-types";
import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import { InterviewerFilter, type FilterValues } from "./InterviewerFilter";

const mockSkills: Skill[] = [
  { id: "1", name: "System Design", slug: "system-design" },
  { id: "2", name: "Data Structures", slug: "data-structures" },
];

describe("InterviewerFilter", () => {
  it("renders filter controls with provided skills", () => {
    const onChange = vi.fn();
    const onReset = vi.fn();
    const values: FilterValues = {};

    render(
      <InterviewerFilter
        skills={mockSkills}
        values={values}
        onChange={onChange}
        onReset={onReset}
      />
    );

    expect(screen.getByRole("combobox", { name: /skill \/ topic/i })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /system design/i })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /data structures/i })).toBeInTheDocument();
  });

  it("calls onChange when skill is selected", () => {
    const onChange = vi.fn();
    const onReset = vi.fn();
    const values: FilterValues = {};

    render(
      <InterviewerFilter
        skills={mockSkills}
        values={values}
        onChange={onChange}
        onReset={onReset}
      />
    );

    const select = screen.getByRole("combobox", { name: /skill \/ topic/i });
    fireEvent.change(select, { target: { value: "system-design" } });

    expect(onChange).toHaveBeenCalledWith({
      skill: "system-design",
    });
  });

  it("calls onChange when experience is entered", () => {
    const onChange = vi.fn();
    const onReset = vi.fn();
    const values: FilterValues = {};

    render(
      <InterviewerFilter
        skills={mockSkills}
        values={values}
        onChange={onChange}
        onReset={onReset}
      />
    );

    const input = screen.getByPlaceholderText("e.g. 5");
    fireEvent.change(input, { target: { value: "7" } });

    expect(onChange).toHaveBeenCalledWith({
      minYearsExperience: 7,
    });
  });

  it("calls onReset when reset button is clicked", () => {
    const onChange = vi.fn();
    const onReset = vi.fn();
    const values: FilterValues = { skill: "system-design" };

    render(
      <InterviewerFilter
        skills={mockSkills}
        values={values}
        onChange={onChange}
        onReset={onReset}
      />
    );

    const resetBtn = screen.getByRole("button", { name: /reset/i });
    fireEvent.click(resetBtn);

    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
