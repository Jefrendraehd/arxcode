"""
Commands for the fashion app.
"""
from server.utils.arx_utils import ArxCommand, list_to_string
from server.utils.prettytable import PrettyTable
from world.dominion.models import Organization
from world.fashion.exceptions import FashionError
from world.fashion.models import FashionSnapshot as Snapshot, FashionOutfit as Outfit, ModusOrnamenta as MO


def get_caller_outfit_from_args(caller, args):
    not_found = "'%s' not found in your collection of outfits." % args
    if not args:
        raise FashionError("Requires an outfit's name.")
    try:
        return caller.player_ob.Dominion.fashion_outfits.get(name__icontains=args)
    except Outfit.MultipleObjectsReturned:
        not_found = "'%s' refers to more than one outfit; please be more specific." % args
        try:
            return caller.player_ob.Dominion.fashion_outfits.get(name__iexact=args)
        except (Outfit.MultipleObjectsReturned, Outfit.DoesNotExist):
            raise FashionError(not_found)
    except Outfit.DoesNotExist:
        raise FashionError(not_found)


class CmdFashionOutfit(ArxCommand):
    """
    Manage outfits made of wearable and wieldable items.

    View Usage:
        outfits [<name>]
        outfits/archives
    Manage Usage:
        outfit/archive <name>
        outfit/create <name>
        outfit/delete <name>

    Viewing: With no switch or name, view your non-archived outfits.
    Similarly, use the archive switch without a name to see archived outfits.
    This table shows an appraisal of outfit worth if it's yet to be modeled,
    or the buzz impact it had when it was. (See 'help model' for modeling.)
    Specify any outfit name with no switches to see the items comprising it.

    Management: Toggle the archive status of an outfit by specifying its name
    after the /archive switch. The /create switch makes a new outfit from
    your currently worn, sheathed, and wielded items. The /delete switch
    deletes an existing outfit, but its items still exist. Note that after
    deleting a modeled outfit, each of its items' "buzz messages" will
    revert to their individual value.
    """
    key = "outfit"
    aliases = ["outfits"]
    help_category = "social"
    archive_switches = ("archive", "archives", "archived")

    def func(self):
        try:
            def get_outfit():
                return get_caller_outfit_from_args(self.caller, self.args)

            if self.check_switches(self.archive_switches):
                if self.args:
                    self.archive_or_restore_outfit(get_outfit())
                else:
                    self.view_outfits(archived=True)
            elif "create" in self.switches:
                self.create_outfit()
            elif "delete" in self.switches:
                self.delete_outfit(get_outfit())
            elif not self.switches:
                self.view_outfits()
            else:
                raise FashionError("Invalid Switch")
        except FashionError as err:
            self.msg(err)

    def view_outfits(self, archived=False):
        """Views elements of one outfit as table, or a table of outfits."""
        if self.args:
            outfit = get_caller_outfit_from_args(self.caller, self.args)
            msg = outfit.table_display
        else:
            outfits = self.caller.dompc.fashion_outfits.filter(archived=archived).order_by('name')
            if len(outfits) < 1:
                status = "archived " if archived else ""
                alt = "regular 'outfits'" if archived else "creating one, or 'outfits/archives'"
                raise FashionError("No %soutfits to display! Try %s instead." % (status, alt))
            outfit_header = "%sOutfit" % ("Archived " if archived else "")
            # TODO: event & vote columns
            table = PrettyTable(("Created", outfit_header, "Appraisal/Buzz"))
            for outfit in outfits:
                date = outfit.db_date_created.strftime("%Y/%m/%d")
                table.add_row((date, outfit.name, outfit.appraisal_or_buzz))
            msg = str(table)
        self.msg(msg)

    def create_outfit(self):
        """Create outfit object, add equipment to it, then display result."""
        if not self.args:
            raise FashionError("Cannot create your shiny new outfit without a name.")
        others = self.caller.player_ob.Dominion.fashion_outfits.filter(name__iexact=self.args)
        if others.exists():
            raise FashionError("You own an outfit named '%s' already." % self.args)
        worn = list(self.caller.worn)
        weapons = list(self.caller.wielded) + list(self.caller.sheathed)
        if not worn and not weapons:
            raise FashionError("Emperor %s's New Clothes? Put something on and try again." % self.caller.player)
        outfit = Outfit.objects.create(name=self.args, owner=self.caller.dompc)
        for weapon in weapons:
            slot = "primary weapon" if weapon.is_wielded else "sheathed weapon"
            outfit.add_fashion_item(item=weapon, slot=slot)
        for item in worn:
            outfit.add_fashion_item(item=item)
        msg = "Created " + outfit.list_display
        self.msg(msg)

    def delete_outfit(self, outfit):
        """Bye bye, outfit object."""
        self.msg("|yDeleting %s|y.|n" % outfit.name)
        outfit.delete()

    def archive_or_restore_outfit(self, outfit):
        """Toggle the archive boolean for wardrobe neatness."""
        outfit.archived = not outfit.archived
        outfit.save()
        verb = "added to" if outfit.archived else "restored from"
        self.msg("%s is %s your outfit archives." % (outfit, verb))


class CmdFashionModel(ArxCommand):
    """
    Model items that can be worn or wielded to earn fame.
    Usage:
        model <item>=<organization>
        model/outfit <outfit>=<organization>
    Leaderboards:
        model[/all]
        model/designers[/all] [<designer name>]
        model/orgs[/all] [<organization>]

    A fashion model tests their composure & performance to earn fame. The
    organization sponsoring the model and the item's designer accrues a portion
    of fame as well. Although masks may be modeled, doing so will reveal the
    model's identity in subsequent item labels and informs.
    Without the /all switch for leaderboards, only Top 20 are displayed.
    """
    key = "model"
    aliases = ["models"]
    help_category = "social"
    leaderboard_switches = ("designer", "designers", "org", "orgs", "model", "models", "all")

    def func(self):
        """Execute model command"""
        try:
            if self.args and not self.switches:
                self.model_item()
            elif "outfit" in self.switches:
                self.model_outfit()
            elif not self.switches or self.check_switches(self.leaderboard_switches):
                self.view_leaderboards()
            else:
                raise FashionError("Invalid Switch")
        except FashionError as err:
            self.msg(err)

    def model_item(self):
        """Models an item to earn fame."""
        if not self.rhs:
            raise FashionError("Please specify <item>=<organization>")
        item = self.caller.search(self.lhs, location=self.caller)
        org = Organization.objects.get_public_org(self.rhs, self.caller)
        if not item or not org:
            return
        player = self.caller.player
        try:
            fame = item.model_for_fashion(player, org)
        except AttributeError:
            raise FashionError("%s is not an item you can model for fashion." % item)
        else:
            self.emit_modeling_result(item, org, fame)

    def model_outfit(self):
        """Models an outfit to earn fame."""
        if not self.rhs:
            raise FashionError("Please specify <outfit>=<organization>")
        outfit = get_caller_outfit_from_args(self.caller, self.lhs)
        org = Organization.objects.get_public_org(self.rhs, self.caller)
        if not outfit or not org:
            return
        fame = outfit.model_outfit_for_fashion(org)
        self.emit_modeling_result(outfit, org, fame)

    def emit_modeling_result(self, thing, org, fame):
        """A local emit and caller message about an outfit/item that has been modeled."""
        player = self.caller.player
        emit = Snapshot.get_emit_msg(player, thing, org, fame)
        self.caller.location.msg_contents(emit)
        success = "For modeling %s{n you earn {c%d{n fame. " % (thing, fame)
        success += "Your prestige is now %d." % player.assets.prestige
        self.msg(success)

    def view_leaderboards(self):
        """Views table of fashion leaders"""
        from django.db.models import Sum, Count, Avg, F, IntegerField
        pretty_headers = ["Fashion Model", "Fame", "Items", "Avg Item Fame"]  # default for top 20 models

        def get_queryset(manager, group_by_string, fame_divisor):
            """Teeny helper function for getting annotated queryset"""
            return (manager.values_list(group_by_string)
                           .annotate(total_fame=Sum(F('fame')/fame_divisor))
                           .annotate(Count('id'))
                           .annotate(avg=Avg(F('fame')/fame_divisor, output_field=IntegerField()))
                           .order_by('-total_fame'))

        if "designer" in self.switches or "designers" in self.switches:
            if self.args:
                designer = self.caller.player.search(self.args)
                if not designer:
                    return
                pretty_headers[0] = "%s Model" % designer
                designer = designer.Dominion
                qs = get_queryset(designer.designer_snapshots, 'fashion_model__player__username',
                                  Snapshot.DESIGNER_FAME_DIVISOR)
            else:
                pretty_headers[0] = "Designer"
                qs = get_queryset(Snapshot.objects, 'designer__player__username', Snapshot.DESIGNER_FAME_DIVISOR)
        elif "org" in self.switches or "orgs" in self.switches:
            if self.args:
                org = Organization.objects.get_public_org(self.args, self.caller)
                if not org:
                    return
                pretty_headers[0] = "%s Model" % org
                qs = get_queryset(org.fashion_snapshots, 'fashion_model__player__username', Snapshot.ORG_FAME_DIVISOR)
            else:
                pretty_headers[0] = "Organization"
                qs = get_queryset(Snapshot.objects, 'org__name', Snapshot.ORG_FAME_DIVISOR)
        else:  # Models by fame
            qs = get_queryset(Snapshot.objects, 'fashion_model__player__username', 1)
        qs = qs[:20] if "all" not in self.switches else qs
        if not qs:
            raise FashionError("Nothing was found.")
        table = PrettyTable(pretty_headers)
        for q in qs:
            # for lowercase names, we'll capitalize them
            if q[0] == q[0].lower():
                q = list(q)
                q[0] = q[0].capitalize()
            table.add_row(q)
        self.msg(str(table))


class CmdAdminFashion(ArxCommand):
    """
    Admin commands for modeling.
    Usage:
        @admin_fashion <item ID#>
        @admin_fashion/delete <snapshot ID#>

    Shows the #IDs of model snapshot that was generated whenever the
    item was modeled. /Delete will remove all status awarded, refund AP,
    and delete the snapshot, effectively reversing the model command.
    """
    key = "@admin_fashion"
    help_category = "admin"
    locks = "cmd:perm(Wizards)"

    def func(self):
        """Execute command"""
        try:
            if not self.args or not self.args.isdigit():
                raise FashionError("Requires an ID #.")
            elif not self.switches:
                self.display_item_snapshots()
            elif "delete" in self.switches:
                self.reverse_snapshot(self.args)
            else:
                raise FashionError("Invalid Switch")
        except FashionError as err:
            self.msg(err)

    def display_item_snapshots(self):
        """displays snapshots"""
        from evennia.objects.models import ObjectDB
        try:
            item = ObjectDB.objects.get(id=self.args)
        except ObjectDB.DoesNotExist:
            raise FashionError("No object found for ID %s." % self.args)
        snapshots = item.fashion_snapshots.all()
        if not snapshots:
            raise FashionError("No snapshot exists for %s." % item)
        self.msg("%s snapshot: %s" % (item, ", ".join(ob.id + " by " + ob.fashion_model for ob in snapshots)))

    def reverse_snapshot(self, snapshot_id):
        """reverses snapshots"""
        try:
            snapshot = Snapshot.objects.get(id=snapshot_id)
        except Snapshot.DoesNotExist:
            raise FashionError("No snapshot with ID# %s." % snapshot_id)
        snapshot.reverse_snapshot()
        self.msg("Snapshot #%s fame/ap has been reversed. Deleting it." % snapshot.id)
        snapshot.delete()
