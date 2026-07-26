import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/wrapper';
import { ModuleToggle } from './ModuleToggle';

describe('ModuleToggle', () => {
  it('renders only the modes it was given', () => {
    renderWithProviders(<ModuleToggle modes={['Grid', 'JSON']} value="Grid" onChange={() => {}} />);
    expect(screen.getByText('Grid')).toBeInTheDocument();
    expect(screen.getByText('JSON')).toBeInTheDocument();
    // A module with no raw document must not offer an XML tab that renders nothing.
    expect(screen.queryByText('XML')).not.toBeInTheDocument();
  });

  it('reports the selected mode', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <ModuleToggle modes={['Grid', 'XML', 'JSON']} value="Grid" onChange={onChange} />,
    );
    await user.click(screen.getByText('XML'));
    expect(onChange).toHaveBeenCalledWith('XML');
  });
});
