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

  it('applies the canonical treatment to the title', () => {
    // Pinned because four different treatments existed before this component;
    // the point of Panel is that there is now exactly one.
    render(<Panel title="System">body</Panel>);
    const title = screen.getByText('System').closest('.ant-card-head-title') as HTMLElement;
    expect(title.style.fontSize).toBe('11px');
    expect(title.style.fontWeight).toBe('700');
    expect(title.style.letterSpacing).toBe('0.12em');
    expect(title.style.textTransform).toBe('uppercase');
  });

  it('leaves the extra slot untouched by the title treatment', () => {
    // The treatment lives on `title`, not `header`, because `header` also wraps
    // `extra` — putting uppercase and letter-spacing there deformed every
    // control passed in, which is how the HIP view toggle ended up shouting.
    render(<Panel title="System" extra={<button>Raw</button>}>body</Panel>);
    const head = screen.getByText('System').closest('.ant-card-head') as HTMLElement;
    expect(head.style.textTransform).toBe('');
    expect(head.style.letterSpacing).toBe('');
  });
});
