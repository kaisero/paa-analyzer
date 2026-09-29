import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ViewToggle } from './ViewToggle';

describe('ViewToggle', () => {
  it('renders only the modes it is given', () => {
    render(<ViewToggle modes={['View', 'JSON']} value="View" onChange={() => {}} />);
    expect(screen.getByText('View')).toBeInTheDocument();
    expect(screen.getByText('JSON')).toBeInTheDocument();
    // A module with no raw document must not offer a Raw tab that renders nothing.
    expect(screen.queryByText('Raw')).not.toBeInTheDocument();
  });

  it('reports the selected mode', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<ViewToggle modes={['View', 'Raw', 'JSON']} value="View" onChange={onChange} />);
    await user.click(screen.getByText('Raw'));
    // antd Segmented passes only the value.
    expect(onChange).toHaveBeenCalledWith('Raw');
  });
});
