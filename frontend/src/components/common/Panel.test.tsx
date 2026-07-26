import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Panel } from './Panel';

describe('Panel', () => {
  it('renders its title and children', () => {
    render(<Panel title="System">body text</Panel>);
    expect(screen.getByText('System')).toBeInTheDocument();
    expect(screen.getByText('body text')).toBeInTheDocument();
  });

  it('renders an extra node in the header', () => {
    render(<Panel title="System" extra={<button>toggle</button>}>body</Panel>);
    const header = screen.getByText('System').closest('.ant-card-head')!;
    expect(header).toContainElement(screen.getByRole('button', { name: 'toggle' }));
  });

  it('uses the canonical header treatment', () => {
    // Pinned because four different treatments existed before this component;
    // the point of Panel is that there is now exactly one.
    // antd nests `.ant-card-head-title` inside an unstyled `.ant-card-head-wrapper`,
    // itself inside the styled `.ant-card-head` — walk to the head, not the
    // title's immediate parent, or every expectation below reads ''.
    render(<Panel title="System">body</Panel>);
    const head = screen.getByText('System').closest('.ant-card-head') as HTMLElement;
    expect(head.style.fontSize).toBe('11px');
    expect(head.style.fontWeight).toBe('700');
    expect(head.style.letterSpacing).toBe('0.12em');
    expect(head.style.textTransform).toBe('uppercase');
  });
});
