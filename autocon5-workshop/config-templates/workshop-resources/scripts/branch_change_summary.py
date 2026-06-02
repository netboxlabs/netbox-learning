from django.contrib.contenttypes.models import ContentType

from extras.scripts import ObjectVar, Script
from netbox_branching.models import Branch, ChangeDiff

__all__ = ('BranchChangeSummary',)


class BranchChangeSummary(Script):
    branch = ObjectVar(
        model=Branch,
        label='Branch',
        description='The branch to summarize changes for',
    )

    class Meta:
        name = 'Branch Change Summary'
        description = 'Summarizes all changes in a branch, filtering out no-op updates'
        commit_default = False
        scheduling_enabled = False

    @staticmethod
    def _fmt_table(rows, headers):
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))
        sep = '  '.join('-' * w for w in col_widths)
        header_line = '  '.join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        lines = [header_line, sep]
        for row in rows:
            lines.append('  '.join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)))
        return lines

    @staticmethod
    def _changed_fields(diff):
        """
        Return {field_name: (before, after)} for the actual changes in this diff.

        When diff.original is available, uses netbox_branching's altered_fields.
        When diff.original is None (Diode writes), compares diff.current (initial
        snapshot / main state) against diff.modified (live branch state) directly.
        Internal _* fields are skipped.
        """
        try:
            fields = diff.altered_fields
            original = diff.original or {}
            modified = diff.modified or {}
            return {f: (original.get(f), modified.get(f)) for f in fields}
        except TypeError:
            pass

        # original is None: current holds the main-state snapshot; modified holds
        # the live branch state. Anything that differs between them is a real change.
        current = diff.current or {}
        modified = diff.modified or {}
        if not modified:
            return {}
        return {
            field: (current.get(field), modified_val)
            for field, modified_val in modified.items()
            if not field.startswith('_') and current.get(field) != modified_val
        }

    def run(self, data, commit):
        branch = data['branch']

        all_diffs = list(
            ChangeDiff.objects.filter(branch=branch)
            .select_related('object_type')
            .order_by('object_type__app_label', 'object_type__model', 'action', 'object_repr')
        )

        real_changes = []
        noop_count = 0
        update_fields = {}  # diff.pk -> {field: (before, after)}

        for diff in all_diffs:
            if diff.action == 'update':
                changes = self._changed_fields(diff)
                if not changes:
                    noop_count += 1
                else:
                    update_fields[diff.pk] = changes
                    real_changes.append(diff)
            else:
                real_changes.append(diff)

        created = [d for d in real_changes if d.action == 'create']
        updated = [d for d in real_changes if d.action == 'update']
        deleted = [d for d in real_changes if d.action == 'delete']

        WIDTH = 72
        lines = []
        lines.append('=' * WIDTH)
        lines.append(f'  Branch Change Summary: {branch}')
        lines.append('=' * WIDTH)

        summary = f'  {len(created)} created  |  {len(updated)} updated  |  {len(deleted)} deleted'
        if noop_count:
            summary += f'  ({noop_count} no-op updates filtered out)'
        lines.append(summary)
        lines.append('')

        def _section(heading, diffs):
            lines.append('-' * WIDTH)
            lines.append(f'  {heading} ({len(diffs)})')
            lines.append('-' * WIDTH)
            if not diffs:
                lines.append('  (none)')
                lines.append('')
                return
            rows = [(d.object_type.app_labeled_name, d.object_repr) for d in diffs]
            for tline in self._fmt_table(rows, ('Object Type', 'Name')):
                lines.append('  ' + tline)
            lines.append('')

        def _section_updated(diffs):
            lines.append('-' * WIDTH)
            lines.append(f'  UPDATED ({len(diffs)})')
            lines.append('-' * WIDTH)
            if not diffs:
                lines.append('  (none)')
                lines.append('')
                return
            rows = []
            for d in diffs:
                changes = update_fields.get(d.pk, {})
                for i, (field, (before, after)) in enumerate(changes.items()):
                    rows.append((
                        d.object_type.app_labeled_name if i == 0 else '',
                        d.object_repr if i == 0 else '',
                        field,
                        str(before),
                        str(after),
                    ))
            for tline in self._fmt_table(rows, ('Object Type', 'Name', 'Field', 'Before', 'After')):
                lines.append('  ' + tline)
            lines.append('')

        _section('CREATED', created)
        _section_updated(updated)
        _section('DELETED', deleted)

        return '\n'.join(lines)
